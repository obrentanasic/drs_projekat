from flask import Blueprint, request, jsonify
from rich import _console
from sqlalchemy.orm import joinedload
from datetime import datetime

from auth import token_required, role_required
from dto import (
    QuizCreateDTO,
    QuizUpdateDTO,
    QuizResponseDTO,
    ErrorResponseDTO
)
from extensions import socketio
from models import (
    db,
    User,
    Quiz,
    QuizQuestion,
    QuizAnswer,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    QUIZ_STATUS_PENDING,
    QUIZ_STATUS_APPROVED,
    QUIZ_STATUS_REJECTED,
    VALID_QUIZ_STATUSES
)
from pdf_report_service import pdf_service
from email_service import email_service
import requests
import logging

from flask_cors import cross_origin



logger = logging.getLogger(__name__)

QUIZ_SERVICE_URL = "http://quiz_service:5001"



quiz_bp = Blueprint('quiz', __name__)


def build_quiz_from_dto(quiz, dto):
    quiz.title = dto.title
    quiz.duration_seconds = dto.duration_seconds
    quiz.questions.clear()
    
    for q_index, question_data in enumerate(dto.questions):
        question = QuizQuestion(
            text=question_data.text,
            points=question_data.points,
            order=q_index
        )
        for a_index, answer_data in enumerate(question_data.answers):
            answer = QuizAnswer(
                text=answer_data.text,
                is_correct=answer_data.is_correct,
                order=a_index
            )
            question.answers.append(answer)
        quiz.questions.append(question)


@quiz_bp.route('/quizzes', methods=['POST'])
@role_required(ROLE_MODERATOR)
def create_quiz(user_id):
    if not request.is_json:
        return jsonify(ErrorResponseDTO(
            error='JSON data je obavezan',
            code='json_required'
        ).dict()), 400
    
    try:
        data = QuizCreateDTO(**request.json)
    except ValueError as e:
        return jsonify(ErrorResponseDTO(
            error=str(e),
            code='validation_error'
        ).dict()), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(ErrorResponseDTO(
            error='Korisnik nije pronađen',
            code='user_not_found'
        ).dict()), 404
    
    quiz = Quiz(
        title=data.title,
        author_id=user.id,
        author_name=f"{user.first_name} {user.last_name}",
        duration_seconds=data.duration_seconds,
        status=QUIZ_STATUS_PENDING
    )
    
    build_quiz_from_dto(quiz, data)
    db.session.add(quiz)
    db.session.commit()
    
    payload = quiz.to_dict(include_questions=True, include_answers=True)
    socketio.emit('new_quiz_pending', payload, room='admin_room')
    
    return jsonify(QuizResponseDTO(**payload).dict()), 201


@quiz_bp.route('/quizzes', methods=['GET'])
@token_required
def list_quizzes(user_id):
    status_filter = request.args.get('status', QUIZ_STATUS_APPROVED).upper()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(ErrorResponseDTO(
            error='Korisnik nije pronađen',
            code='user_not_found'
        ).dict()), 404
    
    query = Quiz.query.options(joinedload(Quiz.questions))
    
    if user.role == ROLE_ADMIN and status_filter in VALID_QUIZ_STATUSES:
        query = query.filter_by(status=status_filter)
    elif user.role == ROLE_ADMIN and status_filter == 'ALL':
        query = query
    else:
        query = query.filter_by(status=QUIZ_STATUS_APPROVED)
    
    quizzes = query.order_by(Quiz.created_at.desc()).all()
    
    return jsonify({
        'quizzes': [quiz.to_summary_dict() for quiz in quizzes],
        'total': len(quizzes)
    }), 200


@quiz_bp.route('/quizzes/mine', methods=['GET'])
@role_required(ROLE_MODERATOR, ROLE_ADMIN)
def list_my_quizzes(user_id):
    quizzes = (
        Quiz.query
        .options(joinedload(Quiz.questions).joinedload(QuizQuestion.answers))
        .filter_by(author_id=user_id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    
    return jsonify({
        'quizzes': [quiz.to_dict(include_questions=True, include_answers=True) for quiz in quizzes]
    }), 200


@quiz_bp.route('/quizzes/<int:quiz_id>', methods=['PUT'])
@role_required(ROLE_MODERATOR, ROLE_ADMIN)
def update_quiz(user_id, quiz_id):
    if not request.is_json:
        return jsonify(ErrorResponseDTO(
            error='JSON data je obavezan',
            code='json_required'
        ).dict()), 400
    
    quiz = Quiz.query.options(joinedload(Quiz.questions).joinedload(QuizQuestion.answers)).get(quiz_id)
    if not quiz:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije pronađen',
            code='quiz_not_found'
        ).dict()), 404
    
    if quiz.author_id != user_id:
        return jsonify(ErrorResponseDTO(
            error='Nemate ovlašćenja za izmenu ovog kviza',
            code='insufficient_permissions'
        ).dict()), 403
    
    if quiz.status != QUIZ_STATUS_REJECTED:
        return jsonify(ErrorResponseDTO(
            error='Samo odbijeni kvizovi mogu biti izmenjeni',
            code='quiz_not_editable'
        ).dict()), 400
    
    try:
        data = QuizUpdateDTO(**request.json)
    except ValueError as e:
        return jsonify(ErrorResponseDTO(
            error=str(e),
            code='validation_error'
        ).dict()), 400
    
    build_quiz_from_dto(quiz, data)
    quiz.status = QUIZ_STATUS_PENDING
    quiz.rejection_reason = None
    db.session.commit()
    
    payload = quiz.to_dict(include_questions=True, include_answers=True)
    socketio.emit('new_quiz_pending', payload, room='admin_room')
    
    return jsonify(QuizResponseDTO(**payload).dict()), 200


@quiz_bp.route('/quizzes/<int:quiz_id>/approve', methods=['POST'])
@role_required(ROLE_ADMIN)
def approve_quiz(user_id, quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije pronađen',
            code='quiz_not_found'
        ).dict()), 404
    
    if quiz.status == QUIZ_STATUS_APPROVED:
        return jsonify(ErrorResponseDTO(
            error='Kviz je već odobren',
            code='quiz_already_approved'
        ).dict()), 400
    
    quiz.status = QUIZ_STATUS_APPROVED
    quiz.rejection_reason = None
    db.session.commit()
    
    # Sync quiz to MongoDB for the Quiz Service
    try:
        quiz_data = quiz.to_dict(include_questions=True, include_answers=True)
        response = requests.post(
            f"{QUIZ_SERVICE_URL}/quizzes/sync",
            json=quiz_data,
            timeout=10
        )
        if response.status_code != 201:
            print(f"Warning: Failed to sync quiz {quiz_id} to MongoDB: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not sync quiz to MongoDB: {e}")
    
    payload = quiz.to_summary_dict()
    socketio.emit('quiz_approved', payload)
    
    return jsonify(payload), 200


@quiz_bp.route('/quizzes/<int:quiz_id>/reject', methods=['POST'])
@role_required(ROLE_ADMIN)
def reject_quiz(user_id, quiz_id):
    if not request.is_json:
        return jsonify(ErrorResponseDTO(
            error='JSON data je obavezan',
            code='json_required'
        ).dict()), 400
    
    reason = (request.json.get('reason') or '').strip()
    if not reason:
        return jsonify(ErrorResponseDTO(
            error='Razlog odbijanja je obavezan',
            code='rejection_reason_required'
        ).dict()), 400
    
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije pronađen',
            code='quiz_not_found'
        ).dict()), 404
    
    quiz.status = QUIZ_STATUS_REJECTED
    quiz.rejection_reason = reason
    db.session.commit()
    
    payload = quiz.to_summary_dict()
    socketio.emit('quiz_rejected', payload)
    
    return jsonify(payload), 200


@quiz_bp.route('/quizzes/<int:quiz_id>/play', methods=['GET'])
@token_required
def get_quiz_for_play(user_id, quiz_id):
    """Get quiz for playing (without correct answers)"""
    from sqlalchemy.orm import joinedload
    
    quiz = Quiz.query.options(
        joinedload(Quiz.questions).joinedload(QuizQuestion.answers)
    ).get(quiz_id)
    
    if not quiz:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije pronađen',
            code='quiz_not_found'
        ).dict()), 404
    
    if quiz.status != QUIZ_STATUS_APPROVED:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije dostupan za igranje',
            code='quiz_not_available'
        ).dict()), 403
    
    # Convert to dict without showing correct answers
    quiz_dict = quiz.to_dict(include_questions=True, include_answers=True)
    
    # Remove is_correct from answers for security
    for question in quiz_dict.get('questions', []):
        for answer in question.get('answers', []):
            answer.pop('is_correct', None)
    
    return jsonify(quiz_dict), 200


@quiz_bp.route('/quizzes/<int:quiz_id>/submit', methods=['POST'])
@token_required
def submit_quiz_answers(user_id, quiz_id):
    """Submit quiz answers - proxied to Quiz Service"""
    if not request.is_json:
        return jsonify(ErrorResponseDTO(
            error='JSON data required',
            code='json_required'
        ).dict()), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify(ErrorResponseDTO(
            error='Korisnik nije pronađen',
            code='user_not_found'
        ).dict()), 404
    
    # Forward to Quiz Service with user info
    data = request.json
    data['user_id'] = str(user_id)
    data['user_email'] = user.email
    data['user_name'] = f"{user.first_name} {user.last_name}"
    
    try:
        response = requests.post(
            f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/submit",
            json=data,
            timeout=10
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        _console.print(f"[red]Error submitting quiz answers: {e}[/red]")
        return jsonify(ErrorResponseDTO(
            error='Quiz service unavailable',
            code='service_unavailable'
        ).dict()), 503


@quiz_bp.route('/quizzes/<int:quiz_id>/leaderboard', methods=['GET'])
@token_required
def get_quiz_leaderboard(user_id, quiz_id):
    """Get quiz leaderboard - proxied to Quiz Service"""
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/results",
            timeout=10
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException:
        return jsonify([]), 200


@quiz_bp.route('/users/my-results', methods=['GET'])
@token_required
def get_my_results(user_id):
    """Get current user's quiz results"""
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_URL}/users/{user_id}/results",
            timeout=10
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException:
        return jsonify([]), 200


@quiz_bp.route('/quizzes/<int:quiz_id>/statistics', methods=['GET'])
@role_required(ROLE_ADMIN, ROLE_MODERATOR)
def get_quiz_stats(user_id, quiz_id):
    """Get quiz statistics"""
    try:
        response = requests.get(
            f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/statistics",
            timeout=10
        )
        return response.json(), response.status_code
    except requests.exceptions.RequestException:
        return jsonify(ErrorResponseDTO(
            error='Statistics unavailable',
            code='service_unavailable'
        ).dict()), 503


@quiz_bp.route('/quizzes/<int:quiz_id>/generate-report', methods=['POST'])
@cross_origin()
@role_required(ROLE_ADMIN)
def generate_quiz_report(user_id, quiz_id):
    """
    Generise PDF Izveštaj o rezultatima kviza i šalje ga administratoru na email
    
    Samo ADMINISTRATOR može generisati Izveštaje
    """
    logger.info(f"Generisanje Izveštaja za kviz {quiz_id} od strane korisnika {user_id}")
    
    # Dohvati korisnika (administratora)
    admin = User.query.get(user_id)
    if not admin:
        return jsonify(ErrorResponseDTO(
            error='Korisnik nije pronađen',
            code='user_not_found'
        ).dict()), 404
    
    # Dohvati kviz
    quiz = Quiz.query.options(
        joinedload(Quiz.questions).joinedload(QuizQuestion.answers)
    ).get(quiz_id)
    
    if not quiz:
        return jsonify(ErrorResponseDTO(
            error='Kviz nije pronađen',
            code='quiz_not_found'
        ).dict()), 404
    
    # Kviz mora biti odobren da bi imao rezultate
    if quiz.status != QUIZ_STATUS_APPROVED:
        return jsonify(ErrorResponseDTO(
            error='Izveštaj se može generisati samo za odobrene kvizove',
            code='quiz_not_approved'
        ).dict()), 400
    
    try:
        # Dohvati rezultate iz Quiz Service-a
        logger.info(f"Dohvatanje rezultata sa {QUIZ_SERVICE_URL}/quizzes/{quiz_id}/results")
        response = requests.get(
            f"{QUIZ_SERVICE_URL}/quizzes/{quiz_id}/results",
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Greška pri dohvatanju rezultata: {response.status_code}")
            return jsonify(ErrorResponseDTO(
                error='Rezultati nisu dostupni',
                code='results_unavailable'
            ).dict()), 503
        
        # Quiz Service vraća direktno listu rezultata
        results_raw = response.json()
        
        # Provjeri tip odgovora
        if isinstance(results_raw, list):
            results_list = results_raw
        else:
            # Fallback ako vraća dictionary sa 'results' ključem
            results_list = results_raw.get('results', [])
        
        logger.info(f"Dohvaćeno {len(results_list)} rezultata")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Greška pri komunikaciji sa Quiz Service: {e}")
        return jsonify(ErrorResponseDTO(
            error='Quiz service nije dostupan',
            code='service_unavailable'
        ).dict()), 503

    # Pripremi podatke za PDF
    quiz_data = quiz.to_dict(include_questions=True, include_answers=True)

    # Izračunaj statistiku
    if results_list:
        scores = [r.get('score', 0) for r in results_list]
        percentages = [r.get('percentage', 0) for r in results_list]
        
        stats = {
            'total_attempts': len(results_list),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'average_percentage': sum(percentages) / len(percentages) if percentages else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_possible_score': sum(q['points'] for q in quiz_data.get('questions', [])),
            'results': results_list
        }
    else:
        # Nema rezultata
        max_possible = sum(q['points'] for q in quiz_data.get('questions', []))
        stats = {
            'total_attempts': 0,
            'average_score': 0,
            'average_percentage': 0,
            'max_score': 0,
            'min_score': 0,
            'max_possible_score': max_possible,
            'results': []
        }
    
    try:
        # Generiši PDF
        logger.info("Generisanje PDF Izveštaja...")
        pdf_buffer = pdf_service.generate_quiz_report(quiz_data, stats)
        
        # Kreiraj filename
        safe_title = "".join(c for c in quiz.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"Izvestaj_{safe_title}_{quiz_id}_{admin.id}_{int(datetime.now().timestamp())}.pdf"
        
        # Pošalji email sa PDF-om
        logger.info(f"Slanje Izveštaja na email: {admin.email}")
        email_sent = email_service.send_pdf_report_email(
            to_email=admin.email,
            first_name=admin.first_name,
            quiz_title=quiz.title,
            pdf_buffer=pdf_buffer,
            filename=filename
        )
        
        if email_sent:
            logger.info(f"Izveštaj uspešno poslan na {admin.email}")
            return jsonify({
                'message': f'PDF Izveštaj je uspešno generisan i poslan na {admin.email}',
                'quiz_id': quiz_id,
                'quiz_title': quiz.title,
                'email': admin.email,
                'total_results': stats['total_attempts'],
                'report_generated_at': datetime.now().isoformat()
            }), 200
        else:
            logger.error("Slanje emaila neuspešno")
            return jsonify(ErrorResponseDTO(
                error='Izveštaj je generisan ali slanje emaila nije uspelo. Provjerite email postavke.',
                code='email_send_failed'
            ).dict()), 500
            
    except Exception as e:
        logger.error(f"Greška pri generisanju Izveštaja: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify(ErrorResponseDTO(
            error=f'Greška pri generisanju Izveštaja: {str(e)}',
            code='report_generation_failed'
        ).dict()), 500
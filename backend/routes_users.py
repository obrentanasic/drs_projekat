from flask import Blueprint, request, jsonify, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import logging
from sqlalchemy import func

from dto import (
    UserRegisterDTO, UserLoginDTO, UserUpdateDTO, UserResponseDTO,
    ChangeRoleDTO, ImageUploadResponseDTO, UserListResponseDTO, UserStatsDTO
)
from models import User, db, ROLE_PLAYER, ROLE_MODERATOR, ROLE_ADMIN
from auth import token_required, role_required
from config import Config

# ✅ DODAJ IMPORT EMAIL SERVISA:
try:
    from email_service import email_service
    logger = logging.getLogger(__name__)
    logger.info("✅ EmailService imported successfully")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to import email_service: {e}")
    # Kreiraj dummy email_service da ne crash-uje aplikacija
    class DummyEmailService:
        def send_role_change_email(self, *args, **kwargs):
            logger.warning("DummyEmailService: Email not sent (service not available)")
            return True
    email_service = DummyEmailService()

# Blueprint
users_bp = Blueprint('users', __name__)

# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    """Provera da li je fajl dozvoljenog formata"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Osigurava da upload folder postoji"""
    upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

def validate_image_file(file):
    """Validacija uploadovanog fajla"""
    if not file or file.filename == '':
        return False, "Nije izabran fajl"
    
    if not allowed_file(file.filename):
        return False, f"Dozvoljeni formati: {', '.join(Config.ALLOWED_EXTENSIONS)}"
    
    # Provera veličine fajla
    file.seek(0, 2)  
    file_size = file.tell()
    file.seek(0)  
    
    if file_size > Config.MAX_FILE_SIZE:
        return False, f"Fajl je prevelik (maksimum {Config.MAX_FILE_SIZE // 1024 // 1024}MB)"
    
    return True, ""

# ==================== USER PROFILE ROUTES ====================

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    """Dobavljanje profila trenutnog korisnika (po specifikaciji)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        return jsonify(UserResponseDTO(**user.to_dict()).dict()), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    """Ažuriranje profila trenutnog korisnika (po specifikaciji)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        data = request.json
        
        # Dozvoljena polja za ažuriranje
        allowed_fields = ['first_name', 'last_name', 'date_of_birth', 
                         'gender', 'country', 'street', 'number']
        
        for field in allowed_fields:
            if field in data and data[field] is not None:
                if field == 'date_of_birth':
                    # Konvertuj string u date
                    setattr(user, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(user, field, data[field])
        
        db.session.commit()
        logger.info(f"Profile updated for user: {user.email}")
        
        return jsonify({
            'message': 'Profil uspešno ažuriran',
            'user': UserResponseDTO(**user.to_dict()).dict()
        }), 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile/upload-image', methods=['POST'])
@token_required
def upload_profile_image(user_id):
    """Upload profilne slike (po specifikaciji)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        # Provera da li postoji fajl
        if 'image' not in request.files:
            return jsonify({'error': 'Nije pronađen fajl'}), 400
        
        file = request.files['image']
        
        # Validacija fajla
        is_valid, error_message = validate_image_file(file)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # Kreiranje jedinstvenog imena
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        upload_folder = ensure_upload_folder()
        file_path = os.path.join(upload_folder, new_filename)
        file.save(file_path)
        
        # Brisanje stare slike ako postoji
        if user.profile_image:
            old_file_path = os.path.join(upload_folder, user.profile_image)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete old image: {e}")
        
        user.profile_image = new_filename
        db.session.commit()
        
        logger.info(f"Profile image uploaded for user: {user.email}")
        
        # Kreiranje response DTO
        response = ImageUploadResponseDTO(
            message="Slika uspešno uploadovana",
            image_url=f"/uploads/profile-pictures/{new_filename}",
            filename=new_filename
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Upload image error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ADMIN ROUTES ====================

@users_bp.route('/users', methods=['GET'])
@role_required(ROLE_ADMIN)
def get_all_users(user_id):
    """Dobavljanje svih korisnika (samo admin - po specifikaciji)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        role_filter = request.args.get('role', type=str)
        
        # Osnovni query
        query = User.query
        
        # Pretraga
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term)) |
                (User.email.ilike(search_term))
            )
        
        # Filter po ulozi
        if role_filter and role_filter in [ROLE_PLAYER, ROLE_MODERATOR, ROLE_ADMIN]:
            query = query.filter_by(role=role_filter)
        
        # Sortiranje
        sort_by = request.args.get('sort_by', 'created_at')
        order = request.args.get('order', 'desc')
        
        if sort_by in ['first_name', 'last_name', 'email', 'role', 'created_at']:
            if order == 'desc':
                query = query.order_by(getattr(User, sort_by).desc())
            else:
                query = query.order_by(getattr(User, sort_by))
        else:
            query = query.order_by(User.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        logger.info(f"Admin {user_id} fetched user list, page {page}")
        
        # Kreiranje response DTO
        response = UserListResponseDTO(
            users=[UserResponseDTO(**user.to_dict()) for user in users],
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pagination.pages
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Get all users error: {e}")
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users/<int:target_user_id>/role', methods=['PUT'])
@role_required(ROLE_ADMIN)
def change_user_role(user_id, target_user_id):
    """Promena uloge korisnika (samo admin - po specifikaciji)"""
    try:
        # Validacija DTO
        data = ChangeRoleDTO(**request.json)
        
        # Pronalazak korisnika
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        # Provera da li admin pokušava da promeni sopstvenu ulogu
        if target_user.id == user_id:
            return jsonify({'error': 'Ne možete promeniti sopstvenu ulogu'}), 400
        
        old_role = target_user.role
        
        # Ako je ista uloga, ne radi ništa
        if old_role == data.role:
            return jsonify({'message': 'Korisnik već ima ovu ulogu'}), 200
        
        target_user.role = data.role
        
        # Ako postaje admin, odblokiraj (opciono)
        if data.role == ROLE_ADMIN:
            target_user.is_blocked = False
            target_user.blocked_until = None
        
        db.session.commit()
        
        logger.info(f"Admin {user_id} changed role for user {target_user.email} from {old_role} to {data.role}")
        
        # ✅ ✅ ✅ DODAJ OVAJ KOD ZA SLANJE EMAILA:
        try:
            logger.info(f"🔄 Attempting to send role change email to {target_user.email}")
            success = email_service.send_role_change_email(
                to_email=target_user.email,
                first_name=target_user.first_name,
                old_role=old_role,
                new_role=data.role
            )
            if success:
                logger.info(f"✅ Role change email SENT to {target_user.email}")
            else:
                logger.warning(f"⚠️ Role change email might not have been sent to {target_user.email}")
        except Exception as email_error:
            logger.error(f"❌ Failed to send role change email to {target_user.email}: {email_error}")
            # Ne vraća grešku - samo loguj
        
        return jsonify({
            'message': f'Uloga korisnika {target_user.email} promenjena iz {old_role} u {data.role}',
            'user': UserResponseDTO(**target_user.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Change role error: {e}")
        return jsonify({'error': str(e)}), 400

@users_bp.route('/users/<int:target_user_id>', methods=['DELETE'])
@role_required(ROLE_ADMIN)
def delete_user(user_id, target_user_id):
    """Brisanje korisnika (samo admin - po specifikaciji)"""
    try:
        # Provera da li admin pokušava da obriše samog sebe
        if target_user_id == user_id:
            return jsonify({'error': 'Ne možete obrisati sopstveni nalog'}), 400
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        # Brisanje profilne slike ako postoji
        if target_user.profile_image:
            upload_folder = ensure_upload_folder()
            image_path = os.path.join(upload_folder, target_user.profile_image)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    logger.warning(f"Failed to delete user image: {e}")
        
        # Brisanje korisnika
        db.session.delete(target_user)
        db.session.commit()
        
        logger.warning(f"Admin {user_id} deleted user {target_user.email} (ID: {target_user_id})")
        
        return jsonify({
            'message': 'Korisnik uspešno obrisan',
            'deleted_user_id': target_user_id,
            'deleted_email': target_user.email
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete user error: {e}")
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users/<int:target_user_id>/block', methods=['PUT'])
@role_required(ROLE_ADMIN)
def toggle_user_block(user_id, target_user_id):
    """Blokiranje/odblokiranje korisnika (samo admin)"""
    try:
        if target_user_id == user_id:
            return jsonify({'error': 'Ne možete blokirati samog sebe'}), 400
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404
        
        data = request.json
        block = data.get('block', True)
        hours = data.get('hours', 24)
        
        if block:
            # Blokiranje
            target_user.is_blocked = True
            target_user.blocked_until = datetime.utcnow() + timedelta(hours=hours)
            action = "blokiran"
            message = f"Korisnik {target_user.email} blokiran na {hours} sati"
        else:
            # Odblokiranje
            target_user.is_blocked = False
            target_user.blocked_until = None
            action = "odblokiran"
            message = f"Korisnik {target_user.email} odblokiran"
        
        db.session.commit()
        
        logger.warning(f"Admin {user_id} {action} user {target_user.email}")
        
        return jsonify({
            'message': message,
            'user': UserResponseDTO(**target_user.to_dict()).dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Block user error: {e}")
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users/stats', methods=['GET'])
@role_required(ROLE_ADMIN)
def get_user_stats(user_id):
    """Statistika korisnika (samo admin)"""
    try:
        # Osnovna statistika
        total_users = User.query.count()
        players = User.query.filter_by(role=ROLE_PLAYER).count()
        moderators = User.query.filter_by(role=ROLE_MODERATOR).count()
        admins = User.query.filter_by(role=ROLE_ADMIN).count()
        blocked_users = User.query.filter_by(is_blocked=True).count()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users = User.query.filter(User.created_at >= week_ago).count()
        
        # Kreiranje response DTO
        stats = UserStatsDTO(
            total_users=total_users,
            players=players,
            moderators=moderators,
            admins=admins,
            blocked_users=blocked_users,
            new_users_last_week=new_users
        )
        
        logger.info(f"Admin {user_id} fetched user stats")
        
        return jsonify(stats.dict()), 200
        
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== TEST ROUTES ====================

@users_bp.route('/test/create-users', methods=['GET'])
def create_test_users():
    """Kreiranje test korisnika za development"""
    
    test_users = [
        {
            'email': 'admin@quizplatform.com',
            'password': 'Admin123!',
            'first_name': 'Admin',
            'last_name': 'User',
            'date_of_birth': '1990-01-01',
            'role': ROLE_ADMIN,
            'country': 'Serbia',
            'gender': 'M'
        },
        {
            'email': 'moderator@quizplatform.com',
            'password': 'Moderator123!',
            'first_name': 'Moderator',
            'last_name': 'User',
            'date_of_birth': '1992-05-15',
            'role': ROLE_MODERATOR,
            'country': 'Serbia',
            'gender': 'M'
        },
        {
            'email': 'player@quizplatform.com',
            'password': 'Player123!',
            'first_name': 'Player',
            'last_name': 'User',
            'date_of_birth': '1995-08-22',
            'role': ROLE_PLAYER,
            'country': 'Serbia',
            'gender': 'Ž',
            'street': 'Main Street',
            'number': '123'
        }
    ]
    
    created_count = 0
    for user_data in test_users:
        existing = User.query.filter_by(email=user_data['email']).first()
        if not existing:
            user = User(
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                date_of_birth=datetime.strptime(user_data['date_of_birth'], '%Y-%m-%d').date(),
                role=user_data['role'],
                country=user_data.get('country'),
                gender=user_data.get('gender'),
                street=user_data.get('street'),
                number=user_data.get('number')
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
    
    return jsonify({
        'message': f'Created {created_count} test users',
        'test_users': test_users
    }), 200
import os
import time
from datetime import datetime
from multiprocessing import Process
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, DESCENDING
from bson.objectid import ObjectId
from bson.errors import InvalidId
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# CONFIG
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://quiz_user:quiz_password@mongodb:27017")
SMTP_HOST = os.getenv("SMTP_SERVER", "quiz_mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("FROM_EMAIL", "noreply@quizplatform.com")

client = MongoClient(MONGO_URL)
db = client["quizplatform_db2"]
quiz_collection = db["quizzes"]
results_collection = db["results"]

# Create indexes
quiz_collection.create_index([("status", 1)])
quiz_collection.create_index([("author_id", 1)])
results_collection.create_index([("quiz_id", 1)])
results_collection.create_index([("user_id", 1)])

def serialize_mongo_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    if "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    if "submitted_at" in doc and isinstance(doc["submitted_at"], datetime):
        doc["submitted_at"] = doc["submitted_at"].isoformat()
    return doc

def send_email(to_email, subject, body):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Email failed: {str(e)}")
        return False

def calculate_score(quiz, user_answers):
    """Calculate quiz score"""
    total_score = 0
    max_score = 0
    
    for question in quiz.get("questions", []):
        max_score += question.get("points", 0)
        question_id = str(question.get("id", ""))
        
        user_answer = user_answers.get(question_id, [])
        if not isinstance(user_answer, list):
            user_answer = [user_answer]
        
        correct_answers = set()
        for idx, answer in enumerate(question.get("answers", [])):
            if answer.get("is_correct", False):
                correct_answers.add(str(idx))
        
        user_answer_set = set(str(ans) for ans in user_answer)
        if user_answer_set == correct_answers:
            total_score += question.get("points", 0)
    
    return total_score, max_score

# ASYNC QUIZ PROCESSING WITH PROCESS
def process_quiz_in_background(mongo_quiz_id, user_id, answers, time_spent, user_email, user_name):
    """Process quiz results in a separate process
    Args:
        mongo_quiz_id: MongoDB ObjectId as string
    """
    try:
        time.sleep(5)  # Simulate processing
        
        process_client = MongoClient(MONGO_URL)
        process_db = process_client["quizplatform_db2"]
        process_quiz_collection = process_db["quizzes"]
        process_results_collection = process_db["results"]
        
        # Find quiz by MongoDB ObjectId
        quiz = process_quiz_collection.find_one({"_id": ObjectId(mongo_quiz_id)})
        if not quiz:
            print(f"Quiz {mongo_quiz_id} not found in MongoDB")
            return
        
        total_score, max_score = calculate_score(quiz, answers)
        
        result_data = {
            "quiz_id": mongo_quiz_id,  # Store MongoDB ObjectId as string
            "quiz_name": quiz.get("name", ""),
            "user_id": user_id,
            "user_name": user_name,
            "answers": answers,
            "score": total_score,
            "max_score": max_score,
            "time_spent": time_spent,
            "submitted_at": datetime.utcnow(),
            "processed": True
        }
        
        process_results_collection.insert_one(result_data)
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        email_body = f"""
        <html>
        <body>
            <h2>Quiz Results</h2>
            <p>Thank you for completing: <strong>{quiz.get('name', '')}</strong></p>
            <p><strong>Your Score:</strong> {total_score} / {max_score} ({percentage:.1f}%)</p>
            <p><strong>Time Spent:</strong> {time_spent} seconds</p>
        </body>
        </html>
        """
        
        send_email(user_email, f"Quiz Results: {quiz.get('name', '')}", email_body)
        print(f"Quiz {mongo_quiz_id} processed for user {user_id}")
        
    except Exception as e:
        print(f"Error processing quiz: {str(e)}")
    finally:
        if 'process_client' in locals():
            process_client.close()

# ENDPOINTS
@app.route("/health", methods=["GET"])
def health():
    try:
        client.admin.command('ping')
        return {"status": "quiz-service-ok", "mongodb": "connected"}, 200
    except:
        return {"status": "error"}, 500

@app.route("/quizzes/sync", methods=["POST"])
def sync_quiz():
    """Sync quiz from main backend to MongoDB"""
    try:
        data = request.json
        required = ["id", "title", "questions"]
        for field in required:
            if field not in data:
                return {"error": f"Missing: {field}"}, 400
        
        # Check if quiz already exists
        existing = quiz_collection.find_one({"quiz_id": data["id"]})
        
        quiz_doc = {
            "quiz_id": data["id"],  # Store original integer ID
            "name": data["title"],
            "duration_seconds": data.get("duration_seconds", 0),
            "author_name": data.get("author_name", ""),
            "status": data.get("status", "APPROVED"),
            "questions": data.get("questions", []),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if existing:
            # Update existing
            quiz_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": quiz_doc}
            )
            return {"message": "Quiz updated", "mongo_id": str(existing["_id"])}, 200
        else:
            # Insert new
            result = quiz_collection.insert_one(quiz_doc)
            return {"message": "Quiz synced", "mongo_id": str(result.inserted_id)}, 201
            
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/quizzes/<quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    """Submit quiz - async processing with multiprocessing.Process"""
    try:
        data = request.json
        required = ["user_id", "answers", "time_spent", "user_email", "user_name"]
        for field in required:
            if field not in data:
                return {"error": f"Missing: {field}"}, 400
        
        # Find quiz by integer quiz_id (not MongoDB ObjectId)
        quiz = quiz_collection.find_one({"quiz_id": int(quiz_id)})
        if not quiz:
            return {"error": "Quiz not found in results database. Make sure the quiz is approved."}, 404
        
        # Start async processing in separate process
        process = Process(
            target=process_quiz_in_background,
            args=(
                str(quiz["_id"]),  # Pass MongoDB ObjectId as string
                data["user_id"],
                data["answers"],
                data["time_spent"],
                data["user_email"],
                data["user_name"]
            )
        )
        process.start()
        
        return {
            "message": "Quiz submitted. Results will be emailed.",
            "status": "processing"
        }, 202
    except ValueError:
        return {"error": "Invalid quiz ID format"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/quizzes/<quiz_id>/results", methods=["GET"])
def get_quiz_results(quiz_id):
    """Get leaderboard for a quiz"""
    try:
        # Find by quiz_id field (integer from main DB)
        quiz = quiz_collection.find_one({"quiz_id": int(quiz_id)})
        if not quiz:
            return jsonify([]), 200
        
        # Use MongoDB _id for results query
        mongo_id = str(quiz["_id"])
        results = list(
            results_collection.find({"quiz_id": mongo_id})
            .sort([("score", DESCENDING), ("time_spent", 1)])
        )
        for r in results:
            serialize_mongo_doc(r)
        return jsonify(results), 200
    except ValueError:
        return jsonify([]), 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/users/<user_id>/results", methods=["GET"])
def get_user_results(user_id):
    """Get all results for a user"""
    try:
        results = list(
            results_collection.find({"user_id": user_id})
            .sort("submitted_at", DESCENDING)
        )
        for r in results:
            serialize_mongo_doc(r)
        return jsonify(results), 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/quizzes/<quiz_id>/statistics", methods=["GET"])
def get_quiz_statistics(quiz_id):
    """Get statistics for a quiz"""
    try:
        # Find by quiz_id field (integer from main DB)
        quiz = quiz_collection.find_one({"quiz_id": int(quiz_id)})
        if not quiz:
            return {
                "quiz_id": quiz_id,
                "total_attempts": 0,
                "average_score": 0,
                "average_time": 0,
                "highest_score": 0,
                "lowest_score": 0
            }, 200
        
        # Use MongoDB _id for results query
        mongo_id = str(quiz["_id"])
        results = list(results_collection.find({"quiz_id": mongo_id}))
        
        if not results:
            return {
                "quiz_id": quiz_id,
                "total_attempts": 0,
                "average_score": 0,
                "average_time": 0,
                "highest_score": 0,
                "lowest_score": 0
            }, 200
        
        scores = [r["score"] for r in results]
        times = [r["time_spent"] for r in results]
        
        return jsonify({
            "quiz_id": quiz_id,
            "total_attempts": len(results),
            "average_score": sum(scores) / len(results),
            "average_time": sum(times) / len(results),
            "highest_score": max(scores),
            "lowest_score": min(scores)
        }), 200
    except ValueError:
        return {"error": "Invalid quiz ID"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
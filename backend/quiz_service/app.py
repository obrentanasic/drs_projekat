import os
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)

# ======================
# CONFIG
# ======================
MONGO_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://quiz_user:quiz_password@mongodb:27017"
)

client = MongoClient(MONGO_URL)
db = client["quizplatform_db2"]
quiz_collection = db["quizzes"]
results_collection = db["results"]

# ======================
# HEALTH CHECK
# ======================
@app.route("/health", methods=["GET"])
def health():
    return {"status": "quiz-service-ok"}, 200

# ======================
# CREATE QUIZ
# ======================
@app.route("/quizzes", methods=["POST"])
def create_quiz():
    data = request.json

    required_fields = ["name", "questions", "duration", "author"]
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing {field}"}, 400

    result = quiz_collection.insert_one(data)

    return {
        "message": "Quiz created",
        "quiz_id": str(result.inserted_id)
    }, 201

# ======================
# GET ALL QUIZZES
# ======================
@app.route("/quizzes", methods=["GET"])
def get_quizzes():
    quizzes = list(quiz_collection.find())

    for q in quizzes:
        q["_id"] = str(q["_id"])

    return jsonify(quizzes)

# ======================
# DELETE QUIZ
# ======================
@app.route("/quizzes/<quiz_id>", methods=["DELETE"])
def delete_quiz(quiz_id):
    quiz_collection.delete_one({"_id": ObjectId(quiz_id)})
    return {"message": "Quiz deleted"}, 200

# ======================
# ASYNC RESULT PROCESSING
# ======================
def process_quiz_async(result_data):
    time.sleep(5)  # simulate long processing
    results_collection.insert_one(result_data)

@app.route("/quizzes/<quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    data = request.json

    result_payload = {
        "quiz_id": quiz_id,
        "user_id": data.get("user_id"),
        "answers": data.get("answers"),
        "score": 0
    }

    threading.Thread(
        target=process_quiz_async,
        args=(result_payload,)
    ).start()

    return {"message": "Quiz submitted. Processing async."}, 202

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory "baza" za test
users_db = [
    {'id': 1, 'email': 'admin@quiz.com', 'password': 'admin123', 'name': 'Admin', 'role': 'ADMIN'},
    {'id': 2, 'email': 'user@quiz.com', 'password': 'user123', 'name': 'Test User', 'role': 'USER'}
]

@app.route('/')
def home():
    return jsonify({
        'message': 'Quiz Platform API',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'register': '/api/register (POST)',
            'login': '/api/login (POST)',
            'users': '/api/users (GET)'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': ['flask', 'cors', 'websocket']
    })

# API RUTE
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    return jsonify({
        'message': 'User registered (test mode)',
        'user': {
            'id': 3,
            'email': data.get('email', 'test@quiz.com'),
            'name': data.get('name', 'New User'),
            'role': 'USER'
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Test credentials
    if email == 'admin@quiz.com' and password == 'admin123':
        token = jwt.encode({
            'user_id': 1,
            'email': email,
            'role': 'ADMIN',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': 1,
                'email': email,
                'name': 'Admin',
                'role': 'ADMIN'
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        'users': [
            {'id': u['id'], 'email': u['email'], 'name': u['name'], 'role': u['role']}
            for u in users_db
        ]
    })

# WebSocket
@socketio.on('connect')
def handle_connect():
    print('WebSocket client connected')
    socketio.emit('message', {'data': 'Connected to Quiz Platform'})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Quiz Platform Server")
    print("📍 Port: 5000")
    print("🔗 Frontend: http://localhost:3000")
    print("📊 Health: http://localhost:5000/health")
    print("🔌 WebSocket: ws://localhost:5000")
    print("=" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

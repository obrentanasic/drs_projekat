from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager
import os
from datetime import datetime
from dotenv import load_dotenv

from config import Config
from models import db
from auth import auth_bp
from routes_users import users_bp

def wait_for_postgres():
    max_retries = 30
    retry_delay = 2
    
    print(" Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                print(" PostgreSQL is ready!")
                return True
        except OperationalError as e:
            print(f" Attempt {i+1}/{max_retries}: PostgreSQL not ready yet...")
            time.sleep(retry_delay)
    
    print(" PostgreSQL connection failed!")
    return False

load_dotenv()

# Inicijalizacija Flask aplikacije
app = Flask(__name__, static_folder='uploads')
app.config.from_object(Config)

# CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# JWT
jwt = JWTManager(app)

# SocketIO
socketio = SocketIO(app, 
                   cors_allowed_origins=Config.CORS_ORIGINS,
                   logger=True,
                   engineio_logger=True,
                   async_mode='eventlet')

# Database
db.init_app(app)

# Funkcija za čekanje PostgreSQL
def wait_for_postgres():
    import time
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError
    
    max_retries = 30
    retry_delay = 2
    
    print(" Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                print("PostgreSQL is ready!")
                return True
        except OperationalError as e:
            print(f" Attempt {i+1}/{max_retries}: PostgreSQL not ready yet...")
            time.sleep(retry_delay)
    
    print(" PostgreSQL connection failed!")
    return False

# Kreiranje tabela i default admina
if wait_for_postgres():
    with app.app_context():
        db.create_all()
        # Kreiraj uploads folder ako ne postoji
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
        if not os.path.exists(os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures')):
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures'))
        
        # Kreiraj default admina
        create_default_admin()
        print(" Database initialized with default admin")
else:
    print(" Exiting due to database connection failure")
    exit(1)


# Kreiranje tabela i default admina
with app.app_context():
    db.create_all()
    # Kreiraj uploads folder ako ne postoji
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
    if not os.path.exists(os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures')):
        os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures'))
    
    # Kreiraj default admina
    create_default_admin()
    print(" Database initialized with default admin")

# Registracija blueprint-ova
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api')

# Ruta za profilne slike
@app.route('/uploads/profile-pictures/<filename>')
def serve_profile_picture(filename):
    """Serviranje profilnih slika"""
    try:
        return send_from_directory(
            os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures'),
            filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Osnovne rute
@app.route('/')
def home():
    return jsonify({
        'message': 'Quiz Platform API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'specification': 'Autentifikacija + Upravljanje korisnicima (do "Rad sa kvizovima")',
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'logout': 'POST /api/auth/logout',
                'refresh': 'POST /api/auth/refresh',
                'validate': 'GET /api/auth/validate'
            },
            'users': {
                'profile': 'GET/PUT /api/profile',
                'upload_image': 'POST /api/profile/upload-image',
                'all_users': 'GET /api/users (ADMIN only)',
                'change_role': 'PUT /api/users/<id>/role (ADMIN only)',
                'delete_user': 'DELETE /api/users/<id> (ADMIN only)',
                'block_user': 'PUT /api/users/<id>/block (ADMIN only)',
                'stats': 'GET /api/users/stats (ADMIN only)'
            },
            'health': 'GET /health',
            'docs': 'GET /docs',
            'test_users': 'GET /api/test/create-users'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db.session.bind else 'disconnected',
        'specification': 'Distribuirani računarski sistemi 2025/2026'
    })

@app.route('/docs')
def api_docs():
    return jsonify({
        'documentation': 'Full API documentation available at / endpoint',
        'specification': 'Autentifikacija + Upravljanje korisnicima (do podnaslova "Rad sa kvizovima")'
    })

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print(f'[WebSocket] Client connected: {request.sid}')
    emit('system_message', {
        'message': 'Connected to Quiz Platform',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'[WebSocket] Client disconnected: {request.sid}')

@socketio.on('admin_notification')
def handle_admin_notification(data):
    """Primanje notifikacija za admina"""
    print(f'[WebSocket] Admin notification: {data}')
    emit('admin_alert', data, room='admin_room')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'Token has expired',
        'code': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'error': 'Invalid token',
        'code': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'error': 'Authorization token is required',
        'code': 'missing_token'
    }), 401

if __name__ == '__main__':
    print("=" * 60)
    print(" QUIZ PLATFORM SERVER")
    print(" Distribuirani računarski sistemi 2025/2026")
    print("=" * 60)
    print(f" Port: {Config.PORT}")
    print(f" API: http://localhost:{Config.PORT}")
    print(f" Health: http://localhost:{Config.PORT}/health")
    print(f" WebSocket: ws://localhost:{Config.PORT}")
    print(f" Database: PostgreSQL (ne SQLite!)")
    print(f" Uploads: {Config.UPLOAD_FOLDER}")
    print("=" * 60)
    print(" Default admin: admin@quizplatform.com / Admin123!")
    print("=" * 60)
    print(" SVE DO 'RAD SA KVIZOVIMA' IMPLEMENTIRANO")
    print("=" * 60)
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=Config.PORT, 
        debug=Config.FLASK_DEBUG,
        allow_unsafe_werkzeug=True
    )
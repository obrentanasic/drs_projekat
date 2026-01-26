import token
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import redis
import jwt
import logging

from config import Config
from models import db, User, create_default_admin, ROLE_ADMIN, ROLE_MODERATOR
from extensions import socketio
from auth import auth_bp
from routes_users import users_bp
from routes_quiz import quiz_bp

load_dotenv()

# Konfiguracija logginga
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicijalizacija Flask aplikacije
app = Flask(__name__, static_folder='uploads')
app.config.from_object(Config)

# CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# JWT
jwt = JWTManager(app)

socketio.init_app(
    app, 
    cors_allowed_origins=Config.CORS_ORIGINS,
    logger=False,
    engineio_logger=False,
    async_mode='threading'
    )

# Database
db.init_app(app)

# Redis za rate limiting (fallback na memory)
use_redis = False
redis_client = None
try:
    redis_client = redis.Redis(
        host='localhost',  # Prvo probaj localhost
        port=6379,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    logger.info("✓ Redis connected on localhost:6379")
    use_redis = True
except redis.ConnectionError:
    logger.warning("Redis not available on localhost, trying without Redis")
    use_redis = False

# Rate Limiter sa fallback na memory
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Uvek koristi memory dok se Redis ne popravi
)

# Custom storage za login attempts (3 pokušaja u 15 minuta)
class LoginRateLimiter:
    """Custom rate limiter za login sa 3 pokušaja u 15 minuta"""
    
    def __init__(self):
        self.attempts_key = "login_attempts"
        self.blocked_key = "login_blocked"
        self.in_memory_storage = {}
        
    def get_attempts(self, identifier):
        """Vraća broj pokušaja za identifier (email ili IP)"""
        if use_redis and redis_client:
            key = f"{self.attempts_key}:{identifier}"
            attempts = redis_client.get(key)
            return int(attempts) if attempts else 0
        else:
            # In-memory fallback
            if identifier in self.in_memory_storage:
                data = self.in_memory_storage[identifier]
                # Proveri da li je isteklo vreme (15 minuta)
                if time.time() - data['timestamp'] < 900:  # 900 sekundi = 15 minuta
                    return data['attempts']
                else:
                    # Izbriši stare podatke
                    del self.in_memory_storage[identifier]
            return 0
    
    def increment_attempts(self, identifier):
        """Povećava broj pokušaja za identifier"""
        if use_redis and redis_client:
            key = f"{self.attempts_key}:{identifier}"
            # Increment sa expire od 15 minuta
            attempts = redis_client.incr(key)
            if attempts == 1:  # Prvi pokušaj
                redis_client.expire(key, 900)  # 15 minuta = 900 sekundi
            return attempts
        else:
            # In-memory fallback
            if identifier not in self.in_memory_storage:
                self.in_memory_storage[identifier] = {
                    'attempts': 0,
                    'timestamp': time.time()
                }
            self.in_memory_storage[identifier]['attempts'] += 1
            self.in_memory_storage[identifier]['timestamp'] = time.time()
            return self.in_memory_storage[identifier]['attempts']
    
    def reset_attempts(self, identifier):
        """Resetuje broj pokušaja za identifier"""
        if use_redis and redis_client:
            key = f"{self.attempts_key}:{identifier}"
            redis_client.delete(key)
            block_key = f"{self.blocked_key}:{identifier}"
            redis_client.delete(block_key)
        else:
            # In-memory fallback
            if identifier in self.in_memory_storage:
                del self.in_memory_storage[identifier]
    
    def is_blocked(self, identifier):
        """Proverava da li je identifier blokiran"""
        if use_redis and redis_client:
            block_key = f"{self.blocked_key}:{identifier}"
            return redis_client.exists(block_key) == 1
        else:
            # In-memory fallback
            if identifier in self.in_memory_storage:
                data = self.in_memory_storage[identifier]
                # Blokiraj ako ima 3+ pokušaja u poslednjih 15 min
                if data['attempts'] >= 3 and (time.time() - data['timestamp']) < 900:
                    return True
            return False
    
    def block_identifier(self, identifier, duration=900):
        """Blokira identifier na određeno vreme (podrazumevano 15 min)"""
        if use_redis and redis_client:
            block_key = f"{self.blocked_key}:{identifier}"
            redis_client.setex(block_key, duration, "blocked")
        else:
            # U memory režimu, već je blokiran u is_blocked logici
            pass
    
    def get_block_time_left(self, identifier):
        """Vraća preostalo vreme blokade u sekundama"""
        if use_redis and redis_client:
            block_key = f"{self.blocked_key}:{identifier}"
            return redis_client.ttl(block_key)
        else:
            # In-memory fallback
            if identifier in self.in_memory_storage:
                data = self.in_memory_storage[identifier]
                if data['attempts'] >= 3:
                    time_passed = time.time() - data['timestamp']
                    time_left = 900 - time_passed  # 15 minuta - proteklo vreme
                    return max(0, int(time_left))
            return 0

# Globalni rate limiter instance
login_limiter = LoginRateLimiter()

# Middleware za proveru blokade pre login endpointa
@app.before_request
def check_login_block():
    """Proverava da li je korisnik blokiran pre nego što pristupi login endpointu"""
    if request.endpoint == 'auth.login':
        # Proveri po IP adresi
        ip_address = get_remote_address()
        
        email = None
        if request.is_json and 'email' in request.json:
            email = request.json['email'].lower()
        
        identifiers = [ip_address]
        if email:
            identifiers.append(email)
        
        for identifier in identifiers:
            if login_limiter.is_blocked(identifier):
                time_left = login_limiter.get_block_time_left(identifier)
                minutes = time_left // 60
                seconds = time_left % 60
                
                return jsonify({
                    'error': 'Account temporarily locked',
                    'message': f'Too many failed login attempts. Please try again in {minutes}m {seconds}s',
                    'code': 'account_locked',
                    'time_left': time_left,
                    'retry_after': f"{minutes}:{seconds:02d}"
                }), 429 
# Funkcija za obradu neuspešnog logina
def handle_failed_login(identifier):
    """Increment pokušaja i blokiraj ako je 3. neuspešan pokušaj"""
    attempts = login_limiter.increment_attempts(identifier)
    
    logger.info(f"Failed login attempt for {identifier}. Attempt #{attempts}")
    
    if attempts >= 3:
        login_limiter.block_identifier(identifier, duration=900)  # 15 minuta
        logger.warning(f"{identifier} BLOCKED for 15 minutes due to 3 failed login attempts")
        
        # Loguj u bazu ako je email (za admin monitoring)
        if '@' in identifier:  # Ako je email
            with app.app_context():
                user = User.query.filter_by(email=identifier).first()
                if user:
                    user.login_attempts = attempts
                    user.last_failed_login = datetime.utcnow()
                    user.is_blocked = True
                    user.blocked_until = datetime.utcnow() + timedelta(minutes=15)
                    db.session.commit()
                    logger.info(f"User {user.email} blocked in database until {user.blocked_until}")

# Funkcija za resetovanje pokušaja nakon uspešnog logina
def handle_successful_login(identifier):
    """Resetuje broj pokušaja nakon uspešnog logina"""
    login_limiter.reset_attempts(identifier)
    
    if '@' in identifier:  # Ako je email
        with app.app_context():
            user = User.query.filter_by(email=identifier).first()
            if user:
                user.login_attempts = 0
                user.is_blocked = False
                user.blocked_until = None
                db.session.commit()
                logger.info(f"Login attempts reset for {user.email}")

# Event handler za failed login (poziva se iz auth.py)
@app.route('/api/auth/login-failed', methods=['POST'])
def login_failed_webhook():
    """Endpoint koji poziva auth.py nakon neuspešnog logina"""
    try:
        data = request.get_json()
        if data and 'identifier' in data:
            identifier = data['identifier'].lower()
            handle_failed_login(identifier)
            return jsonify({'status': 'logged', 'identifier': identifier}), 200
        return jsonify({'error': 'Identifier required'}), 400
    except Exception as e:
        logger.error(f"Login failed webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# Event handler za successful login (poziva se iz auth.py)
@app.route('/api/auth/login-success', methods=['POST'])
def login_success_webhook():
    """Endpoint koji poziva auth.py nakon uspešnog logina"""
    try:
        data = request.get_json()
        if data and 'identifier' in data:
            identifier = data['identifier'].lower()
            handle_successful_login(identifier)
            return jsonify({'status': 'reset', 'identifier': identifier}), 200
        return jsonify({'error': 'Identifier required'}), 400
    except Exception as e:
        logger.error(f"Login success webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# Ruta za proveru statusa blokade (za debugging)
@app.route('/api/auth/login-status/<identifier>')
def login_status(identifier):
    """Debug endpoint za proveru statusa pokušaja"""
    attempts = login_limiter.get_attempts(identifier)
    blocked = login_limiter.is_blocked(identifier)
    time_left = login_limiter.get_block_time_left(identifier)
    
    return jsonify({
        'identifier': identifier,
        'attempts': attempts,
        'blocked': blocked,
        'time_left_seconds': time_left,
        'time_left_human': f"{time_left // 60}m {time_left % 60}s"
    })

# Funkcija za čekanje PostgreSQL
def wait_for_postgres():
    max_retries = 30
    retry_delay = 2
    
    logger.info("Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
                logger.info("PostgreSQL is ready!")
                return True
        except OperationalError as e:
            logger.warning(f"Attempt {i+1}/{max_retries}: PostgreSQL not ready yet...")
            time.sleep(retry_delay)
    
    logger.error("PostgreSQL connection failed!")
    return False

# Kreiranje tabela i default admina
if wait_for_postgres():
    with app.app_context():
        # Kreiraj tabele
        db.create_all()
        
        # Kreiraj uploads folder ako ne postoji
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        profile_pics_dir = os.path.join(Config.UPLOAD_FOLDER, 'profile_pictures')
        if not os.path.exists(profile_pics_dir):
            os.makedirs(profile_pics_dir, exist_ok=True)
        
        # Kreiraj default admina
        try:
            admin = create_default_admin()
            if admin:
                logger.info(f"Default admin created: {admin.email}")
        except Exception as e:
            logger.warning(f"Could not create default admin: {e}")
        
        # Status
        if use_redis:
            logger.info("Rate limiting: Redis")
        else:
            logger.info("Rate limiting: In-memory (Redis not available)")
else:
    logger.error("Exiting due to database connection failure")
    exit(1)

# Registracija blueprint-ova
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api')
app.register_blueprint(quiz_bp, url_prefix='/api')

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
        logger.error(f"Error serving profile picture: {e}")
        return jsonify({'error': str(e)}), 404

# Osnovne rute
@app.route('/')
def home():
    return jsonify({
        'message': 'Quiz Platform API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'specification': 'Autentifikacija + Upravljanje korisnicima',
        'rate_limiting': {
            'login_attempts': '3 attempts per 15 minutes',
            'storage': 'Redis' if use_redis else 'In-memory',
            'block_duration': '15 minutes'
        },
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'logout': 'POST /api/auth/logout',
                'refresh': 'POST /api/auth/refresh',
                'validate': 'GET /api/auth/validate',
                'login_status': 'GET /api/auth/login-status/<identifier>'
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
    redis_status = "connected" if use_redis else "disconnected"
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db.session.bind else 'disconnected',
        'redis': redis_status,
        'rate_limiting': 'active',
        'specification': 'Distribuirani računarski sistemi 2025/2026'
    })

@app.route('/docs')
def api_docs():
    return jsonify({
        'documentation': 'Full API documentation available at / endpoint',
        'specification': 'Autentifikacija + Upravljanje korisnicima',
        'security': {
            'rate_limiting': '3 login attempts per 15 minutes per IP/email',
            'jwt': 'Access + Refresh tokens',
            'block_duration': '15 minutes after 3 failed attempts'
        }
    })

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    token = request.args.get('token')
    if not token:
        emit('error', {'message': 'Authentication required'})
        return False
    
    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        request.user_id = data['user_id']
        request.user_role = data.get('role', 'IGRAČ')
    except jwt.ExpiredSignatureError:
        emit('error', {'message': 'Token expired'})
        return False
    except jwt.InvalidTokenError:
        emit('error', {'message': 'Invalid token'})
        return False
    
    if request.user_role == ROLE_ADMIN:
        join_room('admin_room')
        emit('admin_connected', {
            'user_id': request.user_id,
            'message': 'Admin room joined',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    logger.info(f'WebSocket client connected: {request.sid} ({request.user_role})')
    emit('system_message', {
        'message': 'Connected to Quiz Platform',
        'role': request.user_role,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'WebSocket client disconnected: {request.sid}')

@socketio.on('admin_notification')
def handle_admin_notification(data):
    if request.user_role not in [ROLE_MODERATOR, ROLE_ADMIN]:
        emit('error', {'message': 'Insufficient permissions'})
        return
    
    message = (data or {}).get('message', '')
    notification_type = (data or {}).get('type', 'info')
    
    emit('admin_notification', {
        'message': message,
        'type': notification_type,
        'from_user_id': request.user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room='admin_room')

@socketio.on('join_quiz_room')
def handle_join_quiz_room(data):
    quiz_id = (data or {}).get('quiz_id')
    if quiz_id:
        join_room(f'quiz_{quiz_id}')
        emit('system_message', {
            'message': f'Joined quiz room {quiz_id}',
            'timestamp': datetime.utcnow().isoformat()
        })

@socketio.on('leave_quiz_room')
def handle_leave_quiz_room(data):
    quiz_id = (data or {}).get('quiz_id')
    if quiz_id:
        leave_room(f'quiz_{quiz_id}')
        emit('system_message', {
            'message': f'Left quiz room {quiz_id}',
            'timestamp': datetime.utcnow().isoformat()
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests',
        'retry_after': e.description.get('retry_after', 0) if hasattr(e, 'description') else 60
    }), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
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
    print(f" WebSocket: ws://localhost:{Config.PORT} (threading mode)")
    print(f" Database: PostgreSQL")
    print(f" Rate Limiting: {'Redis' if use_redis else 'In-memory'}")
    print(f" Login attempts: 3 per 15 minutes")
    print(f" Uploads: {Config.UPLOAD_FOLDER}")
    print("=" * 60)
    print(" Default admin: admin@quizplatform.com / Admin123!")
    print("=" * 60)
    print(" RATE LIMITING IMPLEMENTED FOR /api/auth/login")
    print(" SVE DO 'RAD SA KVIZOVIMA' IMPLEMENTIRANO")
    print("=" * 60)
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=Config.PORT, 
        debug=Config.FLASK_DEBUG,
        allow_unsafe_werkzeug=True
    )
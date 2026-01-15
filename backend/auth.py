import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import redis
import logging
import requests
from werkzeug.exceptions import TooManyRequests

from config import Config
from models import User, LoginAttempt, db
from dto import UserLoginDTO, UserRegisterDTO, UserResponseDTO, LoginResponseDTO, RegisterResponseDTO, ErrorResponseDTO

# Kreiranje loggera PRVO
logger = logging.getLogger(__name__)

# Blueprint
auth_bp = Blueprint('auth', __name__)

# Redis konekcija sa fallback-om na localhost
try:
    redis_client = None
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True, socket_connect_timeout=2)
        redis_client.ping()
        logger.info("✓ Redis connected on 'redis' host")
    except:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=2)
        redis_client.ping()
        logger.info("✓ Redis connected on 'localhost'")
except Exception as e:
    logger.warning(f"✗ Redis connection failed: {e}")
    logger.info("⚠ Running without Redis - tokens won't be blacklisted")
    redis_client = None

# ==================== HELPER FUNCTIONS ====================

def add_to_blacklist(token, expires_in):
    """Dodaje token u blacklist (Redis keš)"""
    if not redis_client:
        logger.warning("Redis not available - cannot blacklist token")
        return False
    
    try:
        redis_client.setex(f"blacklist:{token}", expires_in, "1")
        logger.debug(f"Token added to blacklist: {token[:20]}...")
        return True
    except Exception as e:
        logger.error(f"Error adding token to blacklist: {e}")
        return False

def is_token_blacklisted(token):
    """Proverava da li je token u blacklist-u"""
    if not redis_client:
        return False
    try:
        return redis_client.exists(f"blacklist:{token}") > 0
    except Exception as e:
        logger.error(f"Redis error checking blacklist: {e}")
        return False

def record_login_attempt(email, successful, ip_address=None, user_agent=None):
    """Beleženje pokušaja prijave (istorija u PostgreSQL)"""
    try:
        ip_addr = ip_address or request.remote_addr if request else "unknown"
        ua = user_agent or (request.user_agent.string if request and request.user_agent else None)
        
        attempt = LoginAttempt(
            email=email,
            successful=successful,
            ip_address=ip_addr,
            user_agent=ua
        )
        db.session.add(attempt)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error recording login attempt: {e}")
        if db.session:
            db.session.rollback()
        return False

def generate_tokens(user_id, role):
    """Generisanje JWT tokena (po specifikaciji: JWT autentifikacija)"""
    try:
        # Access token
        access_token_payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
            'type': 'access',
            'iat': datetime.utcnow()
        }
        
        access_token = jwt.encode(
            access_token_payload, 
            Config.JWT_SECRET_KEY, 
            algorithm='HS256'
        )
        
        # Refresh token
        refresh_token_payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES),
            'type': 'refresh',
            'iat': datetime.utcnow()
        }
        
        refresh_token = jwt.encode(
            refresh_token_payload,
            Config.JWT_SECRET_KEY,
            algorithm='HS256'
        )
        
        return access_token, refresh_token
        
    except Exception as e:
        logger.error(f"Error generating tokens: {e}")
        raise

def check_login_blocked(identifier):
    """Proverava da li je identifier (email/IP) blokiran"""
    try:
        response = requests.get(
            f'http://localhost:{Config.PORT}/api/auth/login-status/{identifier}',
            timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            return data['blocked'], data['time_left_seconds']
    except Exception as e:
        logger.warning(f"Could not check rate limiting service: {e}")
    
    return False, 0

def report_failed_login(identifier):
    """Prijavi neuspešan login rate limiting servisu"""
    try:
        requests.post(
            f'http://localhost:{Config.PORT}/api/auth/login-failed',
            json={'identifier': identifier},
            timeout=1
        )
    except Exception as e:
        logger.debug(f"Failed to report failed login: {e}")

def report_successful_login(identifier):
    """Prijavi uspešan login rate limiting servisu"""
    try:
        requests.post(
            f'http://localhost:{Config.PORT}/api/auth/login-success',
            json={'identifier': identifier},
            timeout=1
        )
    except Exception as e:
        logger.debug(f"Failed to report successful login: {e}")

# ==================== DECORATORS ====================

def token_required(f):
    """Dekorator za zahteve koji zahtevaju autentifikaciju"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Proveri header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify(ErrorResponseDTO(
                error='Token je obavezan',
                code='token_missing'
            ).dict()), 401
        
        # Proveri da li je token u blacklist-u (Redis keš)
        if is_token_blacklisted(token):
            return jsonify(ErrorResponseDTO(
                error='Token je povučen. Prijavite se ponovo.',
                code='token_revoked'
            ).dict()), 401
        
        try:
            # Dekodiraj token
            data = jwt.decode(
                token, 
                Config.JWT_SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Proveri da li je access token
            if data.get('type') != 'access':
                return jsonify(ErrorResponseDTO(
                    error='Nevalidan tip tokena',
                    code='invalid_token_type'
                ).dict()), 401
                
            current_user_id = data['user_id']
            
        except jwt.ExpiredSignatureError:
            return jsonify(ErrorResponseDTO(
                error='Token je istekao',
                code='token_expired'
            ).dict()), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return jsonify(ErrorResponseDTO(
                error='Nevalidan token',
                code='invalid_token'
            ).dict()), 401
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            return jsonify(ErrorResponseDTO(
                error='Greška pri proveri tokena',
                code='token_validation_error'
            ).dict()), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

def role_required(*roles):
    """Dekorator za zahteve koji zahtevaju specifičnu ulogu"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(user_id, *args, **kwargs):
            user = User.query.get(user_id)
            if not user:
                return jsonify(ErrorResponseDTO(
                    error='Korisnik nije pronađen',
                    code='user_not_found'
                ).dict()), 404
            
            if user.role not in roles:
                logger.warning(f"User {user.email} tried to access role-restricted endpoint")
                return jsonify(ErrorResponseDTO(
                    error='Nemate ovlašćenja za ovu akciju',
                    code='insufficient_permissions'
                ).dict()), 403
            
            return f(user_id, *args, **kwargs)
        return decorated
    return decorator

# ==================== AUTH ROUTES ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registracija novog korisnika (po specifikaciji)"""
    try:
        # Proveri da li postoji JSON
        if not request.is_json:
            return jsonify(ErrorResponseDTO(
                error='JSON data je obavezan',
                code='json_required'
            ).dict()), 400
        
        data = UserRegisterDTO(**request.json)
        
        # Provera da li email već postoji
        if User.query.filter_by(email=data.email).first():
            return jsonify(ErrorResponseDTO(
                error='Email je već registrovan',
                code='email_exists'
            ).dict()), 400
        
        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            country=data.country,
            street=data.street,
            number=data.number,
            role='IGRAČ'  
        )
        
        # Postavljanje lozinke (hešovane!)
        user.set_password(data.password)
        
        # Čuvanje u bazu
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.email} (ID: {user.id})")
        
        # Generisanje tokena odmah nakon registracije
        access_token, refresh_token = generate_tokens(user.id, user.role)
        
        # Kreiraj response DTO
        response = RegisterResponseDTO(
            success=True,
            message='Registracija uspešna',
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponseDTO(**user.to_dict())
        )
        
        return jsonify(response.dict()), 201
        
    except ValueError as e:
        return jsonify(ErrorResponseDTO(
            error=str(e),
            code='validation_error'
        ).dict()), 400
    except Exception as e:
        if db.session:
            db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify(ErrorResponseDTO(
            error='Greška pri registraciji',
            code='registration_error',
            details=str(e) if Config.FLASK_DEBUG else None
        ).dict()), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Prijava korisnika (po specifikaciji: 3 neuspešna pokušaja = blokada 15 minuta)"""
    try:
        # Proveri da li postoji JSON
        if not request.is_json:
            return jsonify(ErrorResponseDTO(
                error='JSON data je obavezan',
                code='json_required'
            ).dict()), 400
        
        # Koristi DTO za validaciju
        data = UserLoginDTO(**request.json)
        email = data.email.lower()
        ip_address = request.remote_addr
        
        logger.info(f"Login attempt from {ip_address} for email: {email}")
        
        blocked, time_left = check_login_blocked(email)
        if blocked:
            minutes = time_left // 60
            seconds = time_left % 60
            logger.warning(f"Blocked login attempt for {email} - {minutes}m {seconds}s remaining")
            
            return jsonify(ErrorResponseDTO(
                error='Nalog je privremeno blokiran',
                code='account_blocked',
                details={
                    'message': f'Previše neuspešnih pokušaja. Pokušajte ponovo za {minutes}m {seconds}s.',
                    'time_left_seconds': time_left,
                    'retry_after': f"{minutes}:{seconds:02d}"
                }
            ).dict()), 429 
        
        # Proveri i po IP adresi
        blocked_ip, _ = check_login_blocked(ip_address)
        if blocked_ip:
            logger.warning(f"Blocked IP login attempt: {ip_address}")
            return jsonify(ErrorResponseDTO(
                error='IP adresa je blokirana',
                code='ip_blocked',
                details={'message': 'Previše neuspešnih pokušaja sa ove IP adrese'}
            ).dict()), 429
        
        # 2. PRONALAŽENJE KORISNIKA
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"User not found: {email}")
            
            # Evidentiraj neuspešan pokušaj u sistem
            report_failed_login(email)
            report_failed_login(ip_address)
            record_login_attempt(email, False, ip_address)
            
            return jsonify(ErrorResponseDTO(
                error='Pogrešan email ili lozinka',
                code='invalid_credentials',
                details={'attempts_left': 2}
            ).dict()), 401
        
        # 3. PROVERA LOZINKE
        if not user.check_password(data.password):
            logger.warning(f"Wrong password for: {email}")
            
            # Evidentiraj neuspešan pokušaj
            report_failed_login(email)
            report_failed_login(ip_address)
            record_login_attempt(email, False, ip_address)
            
            # Ažuriraj u bazi
            user.record_failed_login()
            db.session.commit()
            
            # Proveri koliko pokušaja ima u novom sistemu
            attempts_left = 2  # Default
            try:
                status_resp = requests.get(
                    f'http://localhost:{Config.PORT}/api/auth/login-status/{email}',
                    timeout=2
                )
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    attempts_left = max(0, 2 - status_data.get('attempts', 0))
            except:
                pass
            
            return jsonify(LoginResponseDTO(
                success=False,
                message=f'Pogrešan email ili lozinka. Preostalo pokušaja: {attempts_left}',
                access_token='',
                user=UserResponseDTO(**user.to_dict()),
                attempts_left=attempts_left
            ).dict()), 401
        
        # 4. USPESAN LOGIN
        logger.info(f"Successful login for: {email}")
        
        # Resetuj sve pokušaje
        report_successful_login(email)
        report_successful_login(ip_address)
        
        # Resetuj u bazi
        user.reset_login_attempts()
        record_login_attempt(email, True, ip_address)
        db.session.commit()
        
        # Generisanje tokena
        access_token, refresh_token = generate_tokens(user.id, user.role)
        
        # Kreiraj response DTO
        response = LoginResponseDTO(
            success=True,
            message='Prijava uspešna',
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponseDTO(**user.to_dict())
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify(ErrorResponseDTO(
            error='Greška pri prijavi',
            code='login_error',
            details=str(e) if Config.FLASK_DEBUG else None
        ).dict()), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Osvežavanje access tokena"""
    try:
        if not request.is_json:
            return jsonify(ErrorResponseDTO(
                error='JSON data je obavezan',
                code='json_required'
            ).dict()), 400
            
        refresh_token_value = request.json.get('refresh_token')
        
        if not refresh_token_value:
            return jsonify(ErrorResponseDTO(
                error='Refresh token je obavezan',
                code='refresh_token_missing'
            ).dict()), 400
        
        # Provera da li je token u blacklist-u
        if is_token_blacklisted(refresh_token_value):
            return jsonify(ErrorResponseDTO(
                error='Token je povučen',
                code='token_revoked'
            ).dict()), 401
        
        # Dekodiranje refresh tokena
        try:
            payload = jwt.decode(
                refresh_token_value, 
                Config.JWT_SECRET_KEY, 
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'refresh':
                return jsonify(ErrorResponseDTO(
                    error='Nevalidan tip tokena',
                    code='invalid_token_type'
                ).dict()), 401
                
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify(ErrorResponseDTO(
                error='Refresh token je istekao',
                code='token_expired'
            ).dict()), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid refresh token: {e}")
            return jsonify(ErrorResponseDTO(
                error='Nevalidan refresh token',
                code='invalid_token'
            ).dict()), 401
        
        # Pronalaženje korisnika
        user = User.query.get(user_id)
        if not user:
            return jsonify(ErrorResponseDTO(
                error='Korisnik nije pronađen',
                code='user_not_found'
            ).dict()), 404
        
        # Generisanje novih tokena
        new_access_token, new_refresh_token = generate_tokens(user.id, user.role)
        
        # Dodavanje starog refresh tokena u blacklist
        if redis_client:
            add_to_blacklist(refresh_token_value, Config.JWT_REFRESH_TOKEN_EXPIRES)
        
        # Kreiraj response DTO
        response = LoginResponseDTO(
            success=True,
            message='Token osvežen',
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=UserResponseDTO(**user.to_dict())
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        return jsonify(ErrorResponseDTO(
            error='Greška pri osvežavanju tokena',
            code='refresh_error',
            details=str(e) if Config.FLASK_DEBUG else None
        ).dict()), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(user_id):
    """Odjava korisnika (po specifikaciji)"""
    try:
        # Dobavi token iz headera
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Dodaj token u blacklist (Redis keš)
            if redis_client:
                expires_in = Config.JWT_ACCESS_TOKEN_EXPIRES
                add_to_blacklist(token, expires_in)
            
            logger.info(f"User {user_id} logged out")
            
            return jsonify({
                'success': True,
                'message': 'Uspešna odjava'
            }), 200
        
        return jsonify(ErrorResponseDTO(
            error='Token nije pronađen',
            code='token_missing'
        ).dict()), 400
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify(ErrorResponseDTO(
            error='Greška pri odjavi',
            code='logout_error'
        ).dict()), 500

@auth_bp.route('/validate', methods=['GET'])
@token_required
def validate_token(user_id):
    """Validacija tokena"""
    user = User.query.get(user_id)
    if not user:
        return jsonify(ErrorResponseDTO(
            error='Korisnik nije pronađen',
            code='user_not_found'
        ).dict()), 404
    
    return jsonify({
        'success': True,
        'valid': True,
        'user': UserResponseDTO(**user.to_dict()).dict()
    }), 200

@auth_bp.route('/rate-limit-status/<identifier>', methods=['GET'])
def rate_limit_status(identifier):
    """Public endpoint za proveru statusa rate limitinga"""
    blocked, time_left = check_login_blocked(identifier)
    
    return jsonify({
        'identifier': identifier,
        'blocked': blocked,
        'time_left_seconds': time_left,
        'time_left_human': f"{time_left // 60}m {time_left % 60}s" if time_left > 0 else "0s"
    }), 200
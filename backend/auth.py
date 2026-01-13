import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from functools import wraps
import redis
import logging

from config import Config
from models import User, LoginAttempt, db
from dto import UserLoginDTO, UserRegisterDTO, UserResponseDTO, LoginResponseDTO, RegisterResponseDTO, ErrorResponseDTO

# Blueprint
auth_bp = Blueprint('auth', __name__)

# Redis (za keš - po specifikaciji!)
redis_client = redis.from_url(Config.REDIS_URL)

# Logger
logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================

def add_to_blacklist(token, expires_in):
    """Dodaje token u blacklist (Redis keš)"""
    try:
        redis_client.setex(f"blacklist:{token}", expires_in, "1")
        logger.debug(f"Token added to blacklist: {token[:20]}...")
        return True
    except Exception as e:
        logger.error(f"Error adding token to blacklist: {e}")
        return False

def is_token_blacklisted(token):
    """Proverava da li je token u blacklist-u"""
    return redis_client.exists(f"blacklist:{token}") > 0

def record_login_attempt(email, successful, ip_address=None, user_agent=None):
    """Beleženje pokušaja prijave (istorija u PostgreSQL)"""
    try:
        attempt = LoginAttempt(
            email=email,
            successful=successful,
            ip_address=ip_address or request.remote_addr,
            user_agent=user_agent or (request.user_agent.string if request.user_agent else None)
        )
        db.session.add(attempt)
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error recording login attempt: {e}")
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
        # Koristi DTO za validaciju
        data = UserRegisterDTO(**request.json)
        
        # Provera da li email već postoji
        if User.query.filter_by(email=data.email).first():
            return jsonify(ErrorResponseDTO(
                error='Email je već registrovan',
                code='email_exists'
            ).dict()), 400
        
        # Kreiranje korisnika (po specifikaciji: sva polja)
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
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify(ErrorResponseDTO(
            error='Greška pri registraciji',
            code='registration_error'
        ).dict()), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Prijava korisnika (po specifikaciji: 3 neuspešna pokušaja = blokada 1 minut)"""
    try:
        # Koristi DTO za validaciju
        data = UserLoginDTO(**request.json)
        email = data.email
        
        logger.info(f"Login attempt for email: {email}")
        
        # Pronalaženje korisnika
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.warning(f"User not found: {email}")
            record_login_attempt(email, False)
            return jsonify(ErrorResponseDTO(
                error='Pogrešan email ili lozinka',
                code='invalid_credentials',
                details={'attempts_left': 2}
            ).dict()), 401
        
        # Provera blokade (po specifikaciji)
        if user.is_login_blocked():
            remaining = (user.blocked_until - datetime.utcnow()).seconds
            logger.warning(f"Blocked user tried to login: {email}, remaining: {remaining}s")
            return jsonify(LoginResponseDTO(
                success=False,
                message='Nalog je privremeno blokiran',
                access_token='',
                user=UserResponseDTO(**user.to_dict()),
                blocked=True,
                blocked_until=user.blocked_until.isoformat(),
                remaining_seconds=remaining
            ).dict()), 403
        
        # Provera lozinke
        if not user.check_password(data.password):
            logger.warning(f"Wrong password for: {email}")
            
            # Evidentiraj neuspešan pokušaj
            user.record_failed_login()
            record_login_attempt(email, False)
            db.session.commit()
            
            # Ako je sada blokiran nakon ovog pokušaja
            if user.is_login_blocked():
                remaining = (user.blocked_until - datetime.utcnow()).seconds
                return jsonify(LoginResponseDTO(
                    success=False,
                    message='Previše neuspešnih pokušaja. Nalog blokiran na 1 minut.',
                    access_token='',
                    user=UserResponseDTO(**user.to_dict()),
                    blocked=True,
                    blocked_until=user.blocked_until.isoformat(),
                    remaining_seconds=remaining
                ).dict()), 429
            else:
                attempts_left = 3 - user.login_attempts
                return jsonify(LoginResponseDTO(
                    success=False,
                    message=f'Pogrešan email ili lozinka. Preostalo pokušaja: {attempts_left}',
                    access_token='',
                    user=UserResponseDTO(**user.to_dict()),
                    attempts_left=attempts_left
                ).dict()), 401
        
        #  USPESAN LOGIN
        user.reset_login_attempts()
        record_login_attempt(email, True)
        db.session.commit()
        
        logger.info(f"Successful login for: {email}")
        
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
            error=str(e),
            code='login_error'
        ).dict()), 400

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Osvežavanje access tokena"""
    try:
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
            error=str(e),
            code='refresh_error'
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
            error=str(e),
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

@auth_bp.route('/failed-attempts', methods=['GET'])
def get_failed_attempts():
    """Debug endpoint za proveru neuspješnih pokušaja"""
    # Ovo je samo za development, u produkciji obriši
    result = {}
    for ip_hash, info in failed_attempts.items():
        result[ip_hash] = {
            'count': info['count'],
            'blocked_until': info['blocked_until'].isoformat() if info['blocked_until'] else None,
            'is_blocked': info['blocked_until'] and info['blocked_until'] > datetime.utcnow()
        }
    return jsonify(result), 200
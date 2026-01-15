from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import bcrypt
from flask import current_app

db = SQLAlchemy()

ROLE_PLAYER = 'IGRAČ'
ROLE_MODERATOR = 'MODERATOR'
ROLE_ADMIN = 'ADMINISTRATOR'

VALID_ROLES = [ROLE_PLAYER, ROLE_MODERATOR, ROLE_ADMIN]

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10))
    country = db.Column(db.String(50))
    street = db.Column(db.String(100))
    number = db.Column(db.String(20))
    role = db.Column(db.String(20), default=ROLE_PLAYER, nullable=False)
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Blokada nakon 3 neuspešna pokušaja (po specifikaciji)
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_until = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    last_failed_attempt = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate()
    
    def _validate(self):
        """Validacija podataka pri kreiranju korisnika"""
        # Validacija email-a
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            raise ValueError('Nevalidan format email-a')
        
        # Validacija dužina
        if len(self.first_name) > 50 or len(self.last_name) > 50:
            raise ValueError('Ime i prezime ne mogu biti duži od 50 karaktera')
        
        if len(self.email) > 120:
            raise ValueError('Email ne može biti duži od 120 karaktera')
        
        # Validacija starosti (minimum 13 godina)
        today = datetime.now().date()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        if age < 13:
            raise ValueError('Morate imati najmanje 13 godina')
        
        # Validacija uloge
        if self.role not in VALID_ROLES:
            raise ValueError(f'Uloga mora biti jedna od: {", ".join(VALID_ROLES)}')
    
    def set_password(self, password):
        """Hashovanje lozinke (po specifikaciji: hešovane, ne čitljive)"""
        if len(password) < 8:
            raise ValueError('Lozinka mora imati najmanje 8 karaktera')
        
        # Provera kompleksnosti lozinke
        if not re.search(r'[A-Z]', password):
            raise ValueError('Lozinka mora sadržati bar jedno veliko slovo')
        if not re.search(r'[a-z]', password):
            raise ValueError('Lozinka mora sadržati bar jedno malo slovo')
        if not re.search(r'\d', password):
            raise ValueError('Lozinka mora sadržati bar jedan broj')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Lozinka mora sadržati bar jedan specijalni karakter')
        
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Provera lozinke koristeći bcrypt"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                self.password_hash.encode('utf-8')
            )
        except Exception as e:
            print(f"Password check error: {e}")
            return False
    
    def record_failed_login(self):
        """Evidentiranje neuspešnog pokušaja prijave (po specifikaciji: 3 pokušaja = blokada)"""
        self.login_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        if self.login_attempts >= 3:
            self.is_blocked = True
            
            # Po specifikaciji: 15 minuta (ili 1 minut za testiranje)
            try:
                # Proveri da li smo u test modu (development)
                is_test_mode = current_app.config.get('FLASK_ENV') == 'development' or \
                              current_app.config.get('DEBUG', False)
                
                if is_test_mode:
                    # Test mod: 1 minut (po specifikaciji: "za testiranje na npr. 1 minut")
                    block_minutes = 1
                else:
                    # Production: 15 minuta (po specifikaciji: "privremeno blokirati pristup npr. na 15 minuta")
                    block_minutes = 15
                    
                self.blocked_until = datetime.utcnow() + timedelta(minutes=block_minutes)
                
                print(f"⚠ User {self.email} blocked for {block_minutes} minutes due to 3 failed login attempts")
                
            except Exception:
                # Fallback ako current_app nije dostupan
                block_minutes = 1  # Default test mode
                self.blocked_until = datetime.utcnow() + timedelta(minutes=block_minutes)
    
    def reset_login_attempts(self):
        """Resetovanje brojača neuspešnih pokušaja nakon uspešnog logina"""
        self.login_attempts = 0
        self.is_blocked = False
        self.blocked_until = None
    
    def is_login_blocked(self):
        """Provera da li je korisnik trenutno blokiran za prijavu"""
        if not self.is_blocked or not self.blocked_until:
            return False
        
        current_time = datetime.utcnow()
        
        if current_time >= self.blocked_until:
            # Blokada je istekla - automatski odblokiraj
            self.is_blocked = False
            self.blocked_until = None
            self.login_attempts = 0
            return False
        
        return True
    
    def get_block_time_remaining(self):
        """Vraća preostalo vreme blokade u sekundama"""
        if not self.is_login_blocked():
            return 0
        
        remaining = self.blocked_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))
    
    def to_dict(self):
        """Konvertovanje u dictionary (za DTO)"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'country': self.country,
            'street': self.street,
            'number': self.number,
            'role': self.role,
            'profile_image': self.profile_image,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_blocked': self.is_blocked,
            'blocked_until': self.blocked_until.isoformat() if self.blocked_until else None,
            'login_attempts': self.login_attempts,
            'login_blocked': self.is_login_blocked(),
            'block_time_remaining': self.get_block_time_remaining()
        }
    
    def is_admin(self):
        return self.role == ROLE_ADMIN
    
    def is_moderator(self):
        return self.role == ROLE_MODERATOR
    
    def is_player(self):
        return self.role == ROLE_PLAYER
    
    def block_user(self, hours=24, reason=""):
        """Blokiranje korisnika od strane admina (ne zbog logina, već zbog ponašanja)"""
        self.is_blocked = True
        self.blocked_until = datetime.utcnow() + timedelta(hours=hours)
        # Ovdje možete dodati logiku za čuvanje razloga blokade
    
    def unblock_user(self):
        """Odblokiranje korisnika (od strane admina)"""
        self.is_blocked = False
        self.blocked_until = None
        # Resetuj i login attempts jer se admin odlučio da ga odblokira
        self.login_attempts = 0
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    attempt_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    successful = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} {"success" if self.successful else "failed"}>'

class FailedLoginCounter(db.Model):
    """Dodatna tabela za praćenje neuspešnih pokušaja po IP i email-u"""
    __tablename__ = 'failed_login_counters'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(255), nullable=False, index=True)  # email ili IP
    attempts = db.Column(db.Integer, default=0)
    first_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    blocked_until = db.Column(db.DateTime)
    
    def __init__(self, identifier):
        self.identifier = identifier
    
    def increment(self):
        """Povećava broj pokušaja"""
        self.attempts += 1
        self.last_attempt = datetime.utcnow()
        
        if self.attempts == 1:
            self.first_attempt = datetime.utcnow()
        
        if self.attempts >= 3:
            # Blokiraj na 15 minuta (ili 1 minut za test)
            try:
                is_test_mode = current_app.config.get('FLASK_ENV') == 'development'
                block_minutes = 1 if is_test_mode else 15
                self.blocked_until = datetime.utcnow() + timedelta(minutes=block_minutes)
            except:
                self.blocked_until = datetime.utcnow() + timedelta(minutes=15)  # default
    
    def reset(self):
        """Resetuje brojač"""
        self.attempts = 0
        self.blocked_until = None
    
    def is_blocked(self):
        """Proverava da li je identifier blokiran"""
        if not self.blocked_until:
            return False
        
        if datetime.utcnow() >= self.blocked_until:
            self.reset()
            return False
        
        return True
    
    def get_remaining_time(self):
        """Vraća preostalo vreme blokade"""
        if not self.is_blocked():
            return 0
        
        remaining = self.blocked_until - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))
    
    def __repr__(self):
        return f'<FailedLoginCounter {self.identifier}: {self.attempts} attempts>'

# Funkcija za kreiranje default admina
def create_default_admin():
    """Kreiranje default admin korisnika ako ne postoji (po specifikaciji)"""
    
    admin_email = 'admin@quizplatform.com'
    admin = User.query.filter_by(email=admin_email).first()
    
    if not admin:
        admin = User(
            first_name='Admin',
            last_name='User',
            email=admin_email,
            date_of_birth=datetime(1990, 1, 1).date(),
            gender='Muški',
            role=ROLE_ADMIN,
            country='Serbia',
            street='Admin Street',
            number='1'
        )
        
        try:
            admin.set_password('Admin123!')  # Koristi set_password za validaciju
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Default admin created: {admin_email}")
            print(f"   Password: Admin123! (change in production!)")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin: {e}")
            raise
    
    print(f"ℹ️ Admin already exists: {admin_email}")
    return admin

# Helper funkcije za rate limiting
def get_failed_login_counter(identifier, create_if_missing=True):
    """Dobavlja ili kreira counter za identifier"""
    counter = FailedLoginCounter.query.filter_by(identifier=identifier).first()
    
    if not counter and create_if_missing:
        counter = FailedLoginCounter(identifier=identifier)
        db.session.add(counter)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return None
    
    return counter

def reset_login_counter(identifier):
    """Resetuje counter za identifier"""
    counter = get_failed_login_counter(identifier, create_if_missing=False)
    if counter:
        counter.reset()
        db.session.commit()
        return True
    return False

def is_identifier_blocked(identifier):
    """Proverava da li je identifier (email/IP) blokiran"""
    counter = get_failed_login_counter(identifier, create_if_missing=False)
    if counter:
        return counter.is_blocked()
    return False

def get_remaining_block_time(identifier):
    """Vraća preostalo vreme blokade za identifier"""
    counter = get_failed_login_counter(identifier, create_if_missing=False)
    if counter:
        return counter.get_remaining_time()
    return 0

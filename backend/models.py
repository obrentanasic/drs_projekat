from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import bcrypt 

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
    
   # blokada nakon 3 neuspešna pokušaja
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_until = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    last_failed_attempt = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate()
    
    def _validate(self):
        # Validacija email-a
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            raise ValueError('Nevalidan format email-a')
        
        # Validacija dužina
        if len(self.first_name) > 50 or len(self.last_name) > 50:
            raise ValueError('Ime i prezime ne mogu biti duži od 50 karaktera')
        
        if len(self.email) > 120:
            raise ValueError('Email ne može biti duži od 120 karaktera')
        
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
        """Evidentiranje neuspešnog pokušaja prijave"""
        self.login_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        if self.login_attempts >= 3:
            self.is_blocked = True
            self.blocked_until = datetime.utcnow() + timedelta(minutes=1)  
            self.login_attempts = 0
    
    def reset_login_attempts(self):
        """Resetovanje brojača neuspešnih pokušaja"""
        self.login_attempts = 0
        self.is_blocked = False
        self.blocked_until = None
    
    def is_login_blocked(self):
        """Provera da li je korisnik blokiran"""
        if self.is_blocked and self.blocked_until:
            if datetime.utcnow() < self.blocked_until:
                return True
            else:
                # Blokada je istekla
                self.is_blocked = False
                self.blocked_until = None
                return False
        return False
    
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
            'login_attempts': self.login_attempts
        }
    
    def is_admin(self):
        return self.role == ROLE_ADMIN
    
    def is_moderator(self):
        return self.role == ROLE_MODERATOR
    
    def is_player(self):
        return self.role == ROLE_PLAYER
    
    def block(self, hours=24):
        """Blokiranje korisnika od strane admina"""
        self.is_blocked = True
        self.blocked_until = datetime.utcnow() + timedelta(hours=hours)
    
    def unblock(self):
        """Odblokiranje korisnika"""
        self.is_blocked = False
        self.blocked_until = None
    
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
            role=ROLE_ADMIN,
            country='Serbia'
        )
        admin.password_hash = bcrypt.hashpw('Admin123!'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f" Default admin created: {admin_email}")
        except Exception as e:
            db.session.rollback()
            print(f" Error creating admin: {e}")
    
    return admin
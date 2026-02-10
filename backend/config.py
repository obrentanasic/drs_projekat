import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'quiz-platform-super-secret-key-2024')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    PORT = int(os.getenv('PORT', 5000))
    
    # Flask environment (dodano za rate limiting)
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')  # 'development' ili 'production'
    
    # Database 
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/quizplatform_db1'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-super-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 days
    
    # Redis 
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', '1') == '1'
    RATE_LIMIT_LOGIN_ATTEMPTS = int(os.getenv('RATE_LIMIT_LOGIN_ATTEMPTS', 3))
    
    # Production: "privremeno blokirati pristup npr. na 15 minuta"
    # Test: "za testiranje na npr. 1 minut"
    RATE_LIMIT_BLOCK_MINUTES_PRODUCTION = int(os.getenv('RATE_LIMIT_BLOCK_MINUTES_PRODUCTION', 15))
    RATE_LIMIT_BLOCK_MINUTES_TEST = int(os.getenv('RATE_LIMIT_BLOCK_MINUTES_TEST', 1))
    RATE_LIMIT_BLOCK_SECONDS_PRODUCTION = RATE_LIMIT_BLOCK_MINUTES_PRODUCTION * 60
    RATE_LIMIT_BLOCK_SECONDS_TEST = RATE_LIMIT_BLOCK_MINUTES_TEST * 60
    
    # Helper property za dobijanje trenutnog vremena blokade
    @property
    def RATE_LIMIT_BLOCK_SECONDS(self):
        """Vraća vreme blokade u sekundama u zavisnosti od FLASK_ENV"""
        if self.FLASK_ENV == 'development':
            return self.RATE_LIMIT_BLOCK_SECONDS_TEST
        return self.RATE_LIMIT_BLOCK_SECONDS_PRODUCTION
    
    @property
    def RATE_LIMIT_BLOCK_MINUTES(self):
        """Vraća vreme blokade u minutima u zavisnosti od FLASK_ENV"""
        if self.FLASK_ENV == 'development':
            return self.RATE_LIMIT_BLOCK_MINUTES_TEST
        return self.RATE_LIMIT_BLOCK_MINUTES_PRODUCTION
    
    # Login security (backward compatibility)
    LOGIN_ATTEMPT_LIMIT = RATE_LIMIT_LOGIN_ATTEMPTS  # Alias za backward compatibility
    LOGIN_BLOCK_TIME = RATE_LIMIT_BLOCK_SECONDS  # Alias za backward compatibility
    
    # ✅ DODAJ OVU EMAIL KONFIGURACIJU:
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', '0') == '1'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@quizplatform.com')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5 * 1024 * 1024))  
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Additional security settings
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', '1') == '1'
    PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', '1') == '1'
    PASSWORD_REQUIRE_DIGITS = os.getenv('PASSWORD_REQUIRE_DIGITS', '1') == '1'
    PASSWORD_REQUIRE_SPECIAL = os.getenv('PASSWORD_REQUIRE_SPECIAL', '1') == '1'
    
    # Session settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', '1') == '1'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL = int(os.getenv('WEBSOCKET_PING_INTERVAL', 25))
    WEBSOCKET_PING_TIMEOUT = int(os.getenv('WEBSOCKET_PING_TIMEOUT', 60))
    
    FEATURE_RATE_LIMITING = os.getenv('FEATURE_RATE_LIMITING', '1') == '1'
    FEATURE_EMAIL_NOTIFICATIONS = os.getenv('FEATURE_EMAIL_NOTIFICATIONS', '0') == '1'
    FEATURE_FILE_UPLOAD = os.getenv('FEATURE_FILE_UPLOAD', '1') == '1'
    FEATURE_WEBSOCKET = os.getenv('FEATURE_WEBSOCKET', '1') == '1'
    
    # Helper method za dobijanje rate limit konfiguracije
    def get_rate_limit_config(self):
        """Vraća konfiguraciju za rate limiting kao dict"""
        return {
            'enabled': self.RATE_LIMIT_ENABLED,
            'max_attempts': self.RATE_LIMIT_LOGIN_ATTEMPTS,
            'block_seconds': self.RATE_LIMIT_BLOCK_SECONDS,
            'block_minutes': self.RATE_LIMIT_BLOCK_MINUTES,
            'environment': self.FLASK_ENV,
            'is_test_mode': self.FLASK_ENV == 'development',
            'message': f"Blokada nakon {self.RATE_LIMIT_LOGIN_ATTEMPTS} pokušaja na {self.RATE_LIMIT_BLOCK_MINUTES} minuta"
        }

# Test konfiguracija (za unit testove)
class TestConfig(Config):
    """Konfiguracija za testiranje"""
    TESTING = True
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory baza za testove
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_BLOCK_MINUTES_TEST = 1  # 1 minut za testove
    EMAIL_ENABLED = False  

# Development konfiguracija
class DevelopmentConfig(Config):
    """Konfiguracija za development"""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_BLOCK_MINUTES_TEST = 1
    LOG_LEVEL = 'DEBUG'
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000', 'http://localhost:8080']
    # ✅ Dodaj development SMTP konfiguraciju:
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'quiz_mailhog')  # Default za Docker
    SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))

# Production konfiguracija
class ProductionConfig(Config):
    """Konfiguracija za produkciju"""
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_BLOCK_MINUTES_PRODUCTION = 15
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')

# Factory funkcija za dobijanje konfiguracije
def get_config(config_name=None):
    """
    Factory funkcija za dobijanje konfiguracije
    Usage: app.config.from_object(get_config())
    """
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')
    
    config_map = {
        'testing': TestConfig,
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }
    
    config_class = config_map.get(config_name, config_map['default'])
    return config_class()

config = get_config()
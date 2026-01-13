from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
import redis

# PostgreSQL za DB1 (korisnici)
db = SQLAlchemy()

def init_postgres(app):
    """Inicijalizacija PostgreSQL baze"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ PostgreSQL database initialized")

# Redis za keš i WebSocket 
redis_client = None

def init_redis():
    """Inicijalizacija Redis keš baze"""
    global redis_client
    from backend.config import Config
    redis_client = redis.from_url(Config.REDIS_URL)
    try:
        redis_client.ping()
        print(" Redis cache initialized")
        return True
    except Exception as e:
        print(f" Redis connection failed: {e}")
        return False

# MongoDB za DB2 (kvizovi - za kasnije)
mongo_client = None
mongo_db = None

def init_mongo():
    """Inicijalizacija MongoDB za kvizove"""
    global mongo_client, mongo_db
    mongo_client = MongoClient('mongodb://localhost:27017/')
    mongo_db = mongo_client['quiz_database']
    print("✅ MongoDB initialized (for quiz service)")
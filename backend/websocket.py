from flask_socketio import SocketIO, join_room, leave_room, emit
from flask import request
import jwt
from datetime import datetime
from config import Config

socketio = SocketIO(cors_allowed_origins=Config.CORS_ORIGINS, 
                    logger=True,
                    engineio_logger=True)

def token_required_ws(f):
    """Dekorator za WebSocket autentifikaciju"""
    def wrapped(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            emit('error', {'message': 'Authentication required'})
            return False
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            request.user_id = data['user_id']
            request.user_role = data.get('role', 'IGRAČ')
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            emit('error', {'message': 'Token expired'})
            return False
        except jwt.InvalidTokenError:
            emit('error', {'message': 'Invalid token'})
            return False
    return wrapped

@socketio.on('connect')
@token_required_ws
def handle_connect():
    user_role = request.user_role
    
    if user_role == 'ADMINISTRATOR':
        join_room('admin_room')
        print(f" Admin {request.user_id} connected to admin room")
        emit('admin_connected', {
            'user_id': request.user_id,
            'message': 'Admin room joined',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    emit('connected', {
        'message': 'Connected to Quiz Platform WebSocket',
        'role': user_role,
        'timestamp': datetime.utcnow().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('send_notification')
@token_required_ws
def send_notification(data):
    """Slanje notifikacije adminu (za kasnije - kvizovi)"""
    if request.user_role in ['MODERATOR', 'ADMINISTRATOR']:
        message = data.get('message', '')
        notification_type = data.get('type', 'info')
        
        notification = {
            'message': message,
            'type': notification_type,
            'from_user_id': request.user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        emit('admin_notification', notification, room='admin_room')
        emit('notification_sent', {'success': True})
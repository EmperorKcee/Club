from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from models import db, FanMessage, User
from datetime import datetime

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# Store active users
active_users = {}

# Store chat history (in production, use a database instead)
chat_history = []

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = next((uid for uid, sid in active_users.items() if sid == request.sid), None)
    if user_id:
        del active_users[user_id]
        emit('user_status', {'user_id': user_id, 'status': 'offline'}, broadcast=True)
    print(f"Client disconnected: {request.sid}")

@socketio.on('user_join')
def handle_user_join(data):
    """Handle when a user joins the chat"""
    user_id = data.get('user_id')
    username = data.get('username')
    
    if user_id and username:
        active_users[user_id] = request.sid
        emit('user_status', 
             {'user_id': user_id, 'username': username, 'status': 'online'}, 
             broadcast=True)
        
        # Send chat history to the new user
        emit('chat_history', {'messages': chat_history[-50:]})  # Last 50 messages

@socketio.on('send_message')
def handle_send_message(data):
    """Handle new chat message"""
    user_id = data.get('user_id')
    username = data.get('username')
    message = data.get('message', '').strip()
    
    if not message:
        return
    
    # Create message data
    message_data = {
        'user_id': user_id,
        'username': username,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'avatar': data.get('avatar', '')
    }
    
    # Add to chat history (in production, save to database)
    chat_history.append(message_data)
    
    # Broadcast the message to all connected clients
    emit('new_message', message_data, broadcast=True)

# Add more event handlers as needed for real-time features

# Function to send real-time match updates
def send_match_update(match_data):
    """Send real-time match updates to all connected clients"""
    socketio.emit('match_update', match_data, namespace='/')

# Function to send real-time news update
def send_news_update(news_data):
    """Send real-time news updates to all connected clients"""
    socketio.emit('news_update', news_data, namespace='/')

# Function to get online users count
def get_online_users_count():
    """Get the number of currently online users"""
    return len(active_users)

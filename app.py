import re
import os
import string
import time
import logging
import base64
import hashlib
import csv
from functools import wraps
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse
import uuid

from flask import (Flask, current_app, json, request, jsonify, render_template, redirect, send_file,session, url_for, flash, make_response)
from flask_login import (LoginManager, UserMixin, login_user, logout_user, 
                        login_required, current_user)
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import mysql.connector
import pymysql
import requests
import torch
import imagehash
import ssl
from PIL import Image
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from web3 import Web3

# =============================================
# INITIALIZATION AND CONFIGURATION
# =============================================

app = Flask(__name__)
#from flask_talisman import Talisman
#Talisman(app)

# Configuration
app.secret_key = 'tinotenda'
app.config['UPLOAD_FOLDER'] = "static/uploads"
app.config['PROFILE_PICS_FOLDER'] = "static/profile_pics"
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mp3', 'wav'}
PAYSTACK_SECRET_KEY = "sk_test_ed78162ac6ecfa0caadb9bc3346619e781498fb5"
MODEL_NAME = "MBZUAI/LaMini-T5-738M"
# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)

# Database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'africcase_db'
}

# Initialize extensions
login_manager = LoginManager(app)
socketio = SocketIO(app)
mail = Mail(app)

# =============================================
# HELPER FUNCTIONS
# =============================================

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@africcase.com'

# Initialize extensions
login_manager = LoginManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
mail = Mail(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper functions
def create_connection():
    """Create a database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = create_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, profile_picture FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as err:
        logger.error(f"Error fetching user: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
# Database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'art_showcase'
}

# Initialize extensions
login_manager = LoginManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
mail = Mail(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper functions
def create_connection():
    """Create a database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = create_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, profile_picture FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as err:
        logger.error(f"Error fetching user: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} connected")
        join_room(f"user_{current_user.id}")
    else:
        logger.info("Anonymous user connected")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} disconnected")
        leave_room(f"user_{current_user.id}")

@socketio.on('join_room')
def handle_join_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    # Check if user has access to the room
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if room exists
        cursor.execute("SELECT id, room_type FROM collaboration_rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room:
            emit('error', {'message': 'Room not found'})
            return
            
        # Add user to participants if not already there
        cursor.execute("""
            INSERT IGNORE INTO room_participants (room_id, user_id) 
            VALUES (%s, %s)
        """, (room_id, current_user.id))
        conn.commit()
        
        join_room(room_id)
        logger.info(f"User {current_user.username} joined room {room_id}")
        
        # Notify others in the room
        emit('user_joined', {
            'user_id': current_user.id,
            'username': current_user.username,
            'profile_picture': current_user.profile_picture,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
        # Send current room state to the user
        send_room_state(room_id, request.sid)
        
    except mysql.connector.Error as err:
        logger.error(f"Error joining room: {err}")
        emit('error', {'message': 'Error joining room'})
    finally:
        cursor.close()
        conn.close()

@socketio.on('leave_room')
def handle_leave_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
        
    leave_room(room_id)
    logger.info(f"User {current_user.username} left room {room_id}")
    
    # Update last active time in database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE room_participants 
            SET last_active = NOW() 
            WHERE room_id = %s AND user_id = %s
        """, (room_id, current_user.id))
        conn.commit()
        
        # Notify others in the room
        emit('user_left', {
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error updating participant: {err}")
    finally:
        cursor.close()
        conn.close()

def send_room_state(room_id, sid):
    """Send the current state of a room to a specific user."""
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get room type
        cursor.execute("SELECT room_type FROM collaboration_rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room:
            return
            
        room_type = room['room_type']
        
        # Get participants
        cursor.execute("""
            SELECT u.id, u.username, u.profile_picture 
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = %s
            ORDER BY rp.last_active DESC
        """, (room_id,))
        participants = cursor.fetchall()
        
        # Get chat history (last 50 messages)
        cursor.execute("""
            SELECT cm.id, cm.user_id, u.username, u.profile_picture, 
                   cm.message, cm.message_type, cm.created_at
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.room_id = %s
            ORDER BY cm.created_at DESC
            LIMIT 50
        """, (room_id,))
        messages = cursor.fetchall()
        
        # Get room-specific state
        room_state = {}
        if room_type == 'whiteboard':
            cursor.execute("SELECT canvas_data FROM whiteboard_states WHERE room_id = %s", (room_id,))
            whiteboard = cursor.fetchone()
            room_state['whiteboard'] = whiteboard['canvas_data'] if whiteboard else None
            
        elif room_type == 'document':
            cursor.execute("SELECT title, content FROM document_states WHERE room_id = %s", (room_id,))
            document = cursor.fetchone()
            room_state['document'] = document if document else {
                'title': 'Untitled Document',
                'content': '<h2>Welcome to your shared document!</h2><p>Start collaborating...</p>'
            }
            
        elif room_type == 'project':
            cursor.execute("""
                SELECT id, title, description, status, created_by
                FROM project_tasks
                WHERE room_id = %s
                ORDER BY status, created_at
            """, (room_id,))
            tasks = cursor.fetchall()
            room_state['tasks'] = tasks
            
        elif room_type == 'video':
            # No special state needed for video chat
            pass
            
        # Get shared files
        cursor.execute("""
            SELECT id, name, type, size, uploaded_by, uploaded_at
            FROM shared_files
            WHERE room_id = %s
            ORDER BY uploaded_at DESC
        """, (room_id,))
        files = cursor.fetchall()
        room_state['files'] = files
        
        # Emit the room state to the user
        emit('room_state', {
            'room_id': room_id,
            'room_type': room_type,
            'participants': participants,
            'messages': messages,
            'state': room_state
        }, room=sid)
        
    except mysql.connector.Error as err:
        logger.error(f"Error fetching room state: {err}")
    finally:
        cursor.close()
        conn.close()

# Collaboration tool event handlers
@socketio.on('whiteboard_update')
def handle_whiteboard_update(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    state = data.get('state')
    
    if not room_id or not state:
        return
        
    # Broadcast update to other users in the room
    emit('whiteboard_update', {
        'room_id': room_id,
        'state': state,
        'user_id': current_user.id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id, include_self=False)
    
    # Update canvas state in database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Check if whiteboard state exists
        cursor.execute("SELECT 1 FROM whiteboard_states WHERE room_id = %s", (room_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing state
            cursor.execute("""
                UPDATE whiteboard_states 
                SET canvas_data = %s, last_updated = NOW()
                WHERE room_id = %s
            """, (json.dumps(state), room_id))
        else:
            # Create new state
            cursor.execute("""
                INSERT INTO whiteboard_states (room_id, canvas_data)
                VALUES (%s, %s)
            """, (room_id, json.dumps(state)))
            
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error updating whiteboard: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('document_update')
def handle_document_update(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    title = data.get('state', {}).get('title')
    content = data.get('state', {}).get('content')
    
    if not room_id or not content:
        return
        
    # Broadcast update to other users
    emit('document_update', {
        'room_id': room_id,
        'state': {
            'title': title,
            'content': content
        },
        'user_id': current_user.id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id, include_self=False)
    
    # Update database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Check if document exists
        cursor.execute("SELECT 1 FROM document_states WHERE room_id = %s", (room_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing document
            cursor.execute("""
                UPDATE document_states 
                SET title = %s, content = %s, last_updated = NOW()
                WHERE room_id = %s
            """, (title, json.dumps(content), room_id))
        else:
            # Create new document
            cursor.execute("""
                INSERT INTO document_states (room_id, title, content)
                VALUES (%s, %s, %s)
            """, (room_id, title, json.dumps(content)))
            
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error updating document: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('create_task')
def handle_task_create(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    column = data.get('column')
    task = data.get('task')
    
    if not room_id or not task:
        return
        
    task_id = task.get('id', str(uuid.uuid4()))
    
    # Add to database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO project_tasks (id, room_id, title, description, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (task_id, room_id, task['title'], task.get('description'), column, current_user.id))
        conn.commit()
        
        # Broadcast new task to room
        emit('task_create', {
            'id': task_id,
            'room_id': room_id,
            'title': task['title'],
            'description': task.get('description'),
            'status': column,
            'created_by': current_user.id,
            'creator_username': current_user.username,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error creating task: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('update_task_status')
def handle_task_status_update(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    task_id = data.get('task_id')
    new_status = data.get('new_status')
    
    if not room_id or not task_id or not new_status:
        return
        
    # Update database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE project_tasks 
            SET status = %s, updated_at = NOW()
            WHERE id = %s
        """, (new_status, task_id))
        conn.commit()
        
        # Broadcast update to room
        emit('task_updated', {
            'task': {
                'id': task_id,
                'new_status': new_status
            },
            'room_id': room_id,
            'updated_by': current_user.id,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error updating task status: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('remove_task')
def handle_task_remove(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    task_id = data.get('task_id')
    
    if not room_id or not task_id:
        return
        
    # Delete from database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM project_tasks WHERE id = %s", (task_id,))
        conn.commit()
        
        # Broadcast deletion to room
        emit('task_removed', {
            'task_id': task_id,
            'room_id': room_id,
            'deleted_by': current_user.id,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error deleting task: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    message = data.get('message')
    
    if not room_id or not message:
        return
        
    # Save to database first
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO chat_messages (room_id, user_id, message)
            VALUES (%s, %s, %s)
        """, (room_id, current_user.id, message))
        conn.commit()
        
        # Get the saved message with full details
        cursor.execute("""
            SELECT cm.id, cm.user_id, u.username, u.profile_picture, 
                   cm.message, cm.created_at
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.id = LAST_INSERT_ID()
        """)
        saved_message = cursor.fetchone()
        
        # Broadcast message to room with full details
        emit('new_message', {
            'id': saved_message['id'],
            'user_id': saved_message['user_id'],
            'username': saved_message['username'],
            'profile_picture': saved_message['profile_picture'],
            'message': saved_message['message'],
            'created_at': saved_message['created_at'].isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error saving message: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('typing')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if not room_id:
        return
        
    emit('typing', {
        'user_id': current_user.id,
        'username': current_user.username
    }, room=room_id)

@socketio.on('upload_file')
def handle_file_upload(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    file_data = data.get('file')
    
    if not room_id or not file_data:
        return
        
    file_id = str(uuid.uuid4())
    
    # Save to database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO shared_files (id, room_id, name, type, size, data, uploaded_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (file_id, room_id, file_data['name'], file_data['type'], 
              file_data['size'], file_data['data'], current_user.id))
        conn.commit()
        
        # Broadcast file upload to room
        emit('file_uploaded', {
            'file': {
                'id': file_id,
                'name': file_data['name'],
                'type': file_data['type'],
                'size': file_data['size'],
                'uploaded_by': current_user.username,
                'uploaded_at': datetime.now().isoformat()
            },
            'room_id': room_id
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error saving file: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('delete_file')
def handle_file_delete(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    file_id = data.get('file_id')
    
    if not room_id or not file_id:
        return
        
    # Delete from database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Verify user has permission to delete (either owner or room admin)
        cursor.execute("""
            SELECT 1 FROM shared_files 
            WHERE id = %s AND (uploaded_by = %s OR %s IN (
                SELECT user_id FROM room_admins WHERE room_id = %s
            ))
        """, (file_id, current_user.id, current_user.id, room_id))
        can_delete = cursor.fetchone()
        
        if not can_delete:
            emit('error', {'message': 'You do not have permission to delete this file'}, room=request.sid)
            return
            
        cursor.execute("DELETE FROM shared_files WHERE id = %s", (file_id,))
        conn.commit()
        
        # Broadcast file deletion to room
        emit('file_deleted', {
            'file_id': file_id,
            'room_id': room_id,
            'deleted_by': current_user.id,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error deleting file: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

@socketio.on('refresh_participants')
def handle_refresh_participants(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if not room_id:
        return
        
    # Get current participants
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.username, u.profile_picture 
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = %s
            ORDER BY rp.last_active DESC
        """, (room_id,))
        participants = cursor.fetchall()
        
        # Emit update to room
        emit('user_status_update', {
            'room_id': room_id,
            'users': [p['username'] for p in participants]
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error refreshing participants: {err}")
    finally:
        cursor.close()
        conn.close()

@app.route('/collaboration')
@login_required
def collaboration_hub():
    """Render the collaboration hub page."""
    user = get_current_user()
    user_data = {'role': user.role} 
    conn = create_connection()
    if not conn:
        return render_template('error.html', message="Database connection error"), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get public rooms and rooms the user is in
        cursor.execute("""
            SELECT cr.id, cr.name, cr.description, cr.room_type, 
                   cr.creator_id, u.username as creator_name,
                   COUNT(rp.user_id) as participant_count
            FROM collaboration_rooms cr
            LEFT JOIN room_participants rp ON cr.id = rp.room_id
            JOIN users u ON cr.creator_id = u.id
            WHERE cr.is_private = FALSE OR cr.id IN (
                SELECT room_id FROM room_participants WHERE user_id = %s
            )
            GROUP BY cr.id
            ORDER BY cr.created_at DESC
        """, (current_user.id,))
        rooms = cursor.fetchall()
        
        return render_template('collaboration_hub.html', user=current_user, user_data=user_data, rooms=rooms)
    
    except mysql.connector.Error as err:
        logger.error(f"Error fetching rooms: {err}")
        return render_template('error.html', message="Error loading collaboration hub"), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/collaboration/create', methods=['POST'])
@login_required
def create_collaboration_room():
    """Create a new collaboration room."""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    room_type = data.get('type')
    is_private = data.get('private', False)
    
    if not name or not room_type or room_type not in ['whiteboard', 'document', 'project', 'video']:
        return jsonify({'error': 'Invalid request'}), 400
        
    room_id = str(uuid.uuid4())
    
    conn = create_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        cursor = conn.cursor()
        
        # Create room
        cursor.execute("""
            INSERT INTO collaboration_rooms (id, name, description, room_type, creator_id, is_private)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (room_id, name, description, room_type, current_user.id, is_private))
        
        # Add creator as participant and admin
        cursor.execute("""
            INSERT INTO room_participants (room_id, user_id)
            VALUES (%s, %s)
        """, (room_id, current_user.id))
        
        cursor.execute("""
            INSERT INTO room_admins (room_id, user_id)
            VALUES (%s, %s)
        """, (room_id, current_user.id))
        
        # Initialize room state based on type
        if room_type == 'whiteboard':
            cursor.execute("""
                INSERT INTO whiteboard_states (room_id, canvas_data)
                VALUES (%s, '[]')
            """, (room_id,))
        elif room_type == 'document':
            cursor.execute("""
                INSERT INTO document_states (room_id, title, content)
                VALUES (%s, %s, %s)
            """, (room_id, 'Untitled Document', '<h2>Welcome to your shared document!</h2><p>Start collaborating...</p>'))
            
        conn.commit()
        
        return jsonify({
            'success': True,
            'room_id': room_id,
            'redirect': url_for('collaboration_room', room_id=room_id)
        })
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Error creating room: {err}")
        return jsonify({'error': 'Error creating room'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/collaboration/invite', methods=['POST'])
@login_required
def invite_to_room():
    """Invite users to a collaboration room."""
    data = request.get_json()
    room_id = data.get('room_id')
    emails = data.get('emails')  # Array of email addresses
    message = data.get('message', '')
    
    if not room_id or not emails or not isinstance(emails, list):
        return jsonify({'error': 'Invalid request'}), 400
        
    conn = create_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verify user has permission to invite (is participant)
        cursor.execute("""
            SELECT 1 FROM room_participants 
            WHERE room_id = %s AND user_id = %s
        """, (room_id, current_user.id))
        is_participant = cursor.fetchone()
        
        if not is_participant:
            return jsonify({'error': 'You are not a participant in this room'}), 403
            
        # Get room info
        cursor.execute("""
            SELECT name, is_private FROM collaboration_rooms WHERE id = %s
        """, (room_id,))
        room = cursor.fetchone()
        
        if not room:
            return jsonify({'error': 'Room not found'}), 404
            
        # Create invitations
        invitations = []
        for email in emails:
            # Check if user exists
            cursor.execute("SELECT id, username FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            token = str(uuid.uuid4())
            invitation_id = str(uuid.uuid4())
            
            if user:
                # User exists - add to room if not already a participant
                cursor.execute("""
                    INSERT IGNORE INTO room_participants (room_id, user_id)
                    VALUES (%s, %s)
                """, (room_id, user['id']))
                
                # Create invitation record
                cursor.execute("""
                    INSERT INTO room_invitations (id, room_id, sender_id, recipient_email, token, status)
                    VALUES (%s, %s, %s, %s, %s, 'accepted')
                """, (invitation_id, room_id, current_user.id, email, token))
                
                # Notify user via WebSocket if online
                socketio.emit('room_invitation', {
                    'room_id': room_id,
                    'room_name': room['name'],
                    'inviter': current_user.username,
                    'message': message
                }, room=f"user_{user['id']}")
            else:
                # User doesn't exist - create pending invitation
                cursor.execute("""
                    INSERT INTO room_invitations (id, room_id, sender_id, recipient_email, token)
                    VALUES (%s, %s, %s, %s, %s)
                """, (invitation_id, room_id, current_user.id, email, token))
                
                # Send invitation email
                send_invitation_email(email, room_id, room['name'], current_user.username, token, message)
                
            invitations.append({
                'email': email,
                'token': token,
                'status': 'accepted' if user else 'pending'  # Corrected Python ternary syntax
            })
            
        conn.commit()
        
        return jsonify({
            'success': True,
            'invitations': invitations
        })
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Error creating invitations: {err}")
        return jsonify({'error': 'Error creating invitations'}), 500
    finally:
        cursor.close()
        conn.close()

def send_invitation_email(email, room_id, room_name, sender_name, token, message=''):
    """Send an invitation email."""
    try:
        accept_url = url_for('accept_invitation', token=token, _external=True)
        
        # Use Python string formatting with conditional
        message_part = f'<p>Message from {sender_name}: {message}</p>' if message else ''
        
        msg = Message(
            subject=f"Invitation to join '{room_name}' on Africcase",
            recipients=[email],
            html=f"""
                <h2>You've been invited to collaborate!</h2>
                <p>{sender_name} has invited you to join the room "{room_name}" on Africcase.</p>
                {message_part}
                <p>Click the link below to accept the invitation:</p>
                <p><a href="{accept_url}">{accept_url}</a></p>
                <p>If you don't have an account yet, you'll be prompted to create one.</p>
            """
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending invitation email: {e}")
        return False

@app.route('/collaboration/invite/accept/<token>')
def accept_invitation(token):
    """Handle invitation acceptance."""
    conn = create_connection()
    if not conn:
        return render_template('error.html', message="Database connection error"), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get invitation
        cursor.execute("""
            SELECT ri.*, cr.name as room_name, u.username as sender_name
            FROM room_invitations ri
            JOIN collaboration_rooms cr ON ri.room_id = cr.id
            JOIN users u ON ri.sender_id = u.id
            WHERE ri.token = %s AND ri.status = 'pending' AND ri.expires_at > NOW()
        """, (token,))
        invitation = cursor.fetchone()
        
        if not invitation:
            return render_template('error.html', message="Invalid or expired invitation"), 400
            
        if current_user.is_authenticated:
            # Add user to room
            cursor.execute("""
                INSERT IGNORE INTO room_participants (room_id, user_id)
                VALUES (%s, %s)
            """, (invitation['room_id'], current_user.id))
            
            # Update invitation status
            cursor.execute("""
                UPDATE room_invitations 
                SET status = 'accepted', accepted_at = NOW()
                WHERE id = %s
            """, (invitation['id'],))
            
            conn.commit()
            
            return redirect(url_for('collaboration_room', room_id=invitation['room_id']))
        else:
            # Store invitation in session for after login
            session['pending_invitation'] = token
            return redirect(url_for('login', next=url_for('accept_invitation', token=token)))
    except mysql.connector.Error as err:
        conn.rollback()
        logger.error(f"Error accepting invitation: {err}")
        return render_template('error.html', message="Error accepting invitation"), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/collaboration/files/<file_id>')
@login_required
def download_shared_file(file_id):
    """Download a shared file."""
    conn = create_connection()
    if not conn:
        return render_template('error.html', message="Database connection error"), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get file info
        cursor.execute("""
            SELECT f.name, f.type, f.size, f.data, f.room_id
            FROM shared_files f
            JOIN room_participants rp ON f.room_id = rp.room_id
            WHERE f.id = %s AND rp.user_id = %s
        """, (file_id, current_user.id))
        file = cursor.fetchone()
        
        if not file:
            return render_template('error.html', message="File not found or access denied"), 404
            
        # Send file data
        file_data = base64.b64decode(file['data'])
        response = make_response(file_data)
        response.headers.set('Content-Type', file['type'])
        response.headers.set('Content-Disposition', 'attachment', filename=file['name'])
        
        return response
    except mysql.connector.Error as err:
        logger.error(f"Error fetching file: {err}")
        return render_template('error.html', message="Error downloading file"), 500
    finally:
        cursor.close()
        conn.close()

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} connected")
    else:
        logger.info("Anonymous user connected")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} disconnected")
    else:
        logger.info("Anonymous user disconnected")

@socketio.on('join_room')
def handle_join_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    # Check if user has access to the room
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Check if room exists
        cursor.execute("SELECT id FROM collaboration_rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room:
            emit('error', {'message': 'Room not found'})
            return
            
        # Add user to participants if not already there
        cursor.execute("""
            INSERT IGNORE INTO room_participants (room_id, user_id) 
            VALUES (%s, %s)
        """, (room_id, current_user.id))
        conn.commit()
        
        join_room(room_id)
        logger.info(f"User {current_user.username} joined room {room_id}")
        
        # Notify others in the room
        emit('user_joined', {
            'user_id': current_user.id,
            'username': current_user.username,
            'profile_picture': current_user.profile_picture,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
        # Send current room state to the user
        send_room_state(room_id, current_user.id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error joining room: {err}")
        emit('error', {'message': 'Error joining room'})
    finally:
        cursor.close()
        conn.close()

@socketio.on('leave_room')
def handle_leave_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
        
    leave_room(room_id)
    logger.info(f"User {current_user.username} left room {room_id}")
    
    # Update last active time in database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE room_participants 
            SET last_active = NOW() 
            WHERE room_id = %s AND user_id = %s
        """, (room_id, current_user.id))
        conn.commit()
        
        # Notify others in the room
        emit('user_left', {
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.now().isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error updating participant: {err}")
    finally:
        cursor.close()
        conn.close()

def send_room_state(room_id, user_id):
    """Send the current state of a room to a specific user."""
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get room type
        cursor.execute("SELECT room_type FROM collaboration_rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room:
            return
            
        room_type = room['room_type']
        
        # Get participants
        cursor.execute("""
            SELECT u.id, u.username, u.profile_picture 
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = %s
            ORDER BY rp.last_active DESC
        """, (room_id,))
        participants = cursor.fetchall()
        
        # Get chat history (last 50 messages)
        cursor.execute("""
            SELECT cm.id, cm.user_id, u.username, u.profile_picture, 
                   cm.message, cm.message_type, cm.created_at
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.room_id = %s
            ORDER BY cm.created_at DESC
            LIMIT 50
        """, (room_id,))
        messages = cursor.fetchall()
        
        # Get room-specific state
        room_state = {}
        if room_type == 'whiteboard':
            cursor.execute("SELECT canvas_data FROM whiteboard_states WHERE room_id = %s", (room_id,))
            whiteboard = cursor.fetchone()
            room_state['whiteboard'] = whiteboard['canvas_data'] if whiteboard else None
            
        elif room_type == 'document':
            cursor.execute("SELECT title, content FROM document_states WHERE room_id = %s", (room_id,))
            document = cursor.fetchone()
            room_state['document'] = document if document else {
                'title': 'Untitled Document',
                'content': '<h2>Welcome to your shared document!</h2><p>Start collaborating...</p>'
            }
            
        elif room_type == 'project':
            cursor.execute("""
                SELECT id, title, description, status, created_by
                FROM project_tasks
                WHERE room_id = %s
                ORDER BY status, created_at
            """, (room_id,))
            tasks = cursor.fetchall()
            room_state['tasks'] = tasks
            
        # Emit the room state to the user
        emit('room_state', {
            'room_id': room_id,
            'room_type': room_type,
            'participants': participants,
            'messages': messages,
            'state': room_state
        }, room=request.sid)
        
    except mysql.connector.Error as err:
        logger.error(f"Error fetching room state: {err}")
    finally:
        cursor.close()
        conn.close()

# Collaboration tool event handlers
@socketio.on('whiteboard_draw')
def handle_whiteboard_draw(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    path_data = data.get('path')
    
    if not room_id or not path_data:
        return
        
    # Broadcast drawing to other users in the room
    emit('whiteboard_draw', {
        'user_id': current_user.id,
        'path': path_data,
        'timestamp': datetime.now().isoformat()
    }, room=room_id, include_self=False)
    
    # Update canvas state in database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Check if whiteboard state exists
        cursor.execute("SELECT 1 FROM whiteboard_states WHERE room_id = %s", (room_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing state
            cursor.execute("""
                UPDATE whiteboard_states 
                SET canvas_data = JSON_ARRAY_APPEND(canvas_data, '$', %s)
                WHERE room_id = %s
            """, (json.dumps(path_data), room_id))
        else:
            # Create new state
            cursor.execute("""
                INSERT INTO whiteboard_states (room_id, canvas_data)
                VALUES (%s, %s)
            """, (room_id, json.dumps([path_data])))
            
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error updating whiteboard: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('whiteboard_clear')
def handle_whiteboard_clear(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if not room_id:
        return
        
    # Broadcast clear to other users
    emit('whiteboard_clear', {
        'user_id': current_user.id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
    
    # Update database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE whiteboard_states 
            SET canvas_data = '[]', last_updated = NOW()
            WHERE room_id = %s
        """, (room_id,))
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error clearing whiteboard: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('document_update')
def handle_document_update(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    title = data.get('title')
    content = data.get('content')
    
    if not room_id or not content:
        return
        
    # Broadcast update to other users
    emit('document_update', {
        'user_id': current_user.id,
        'title': title,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }, room=room_id, include_self=False)
    
    # Update database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Check if document exists
        cursor.execute("SELECT 1 FROM document_states WHERE room_id = %s", (room_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing document
            cursor.execute("""
                UPDATE document_states 
                SET title = %s, content = %s, last_updated = NOW()
                WHERE room_id = %s
            """, (title, content, room_id))
        else:
            # Create new document
            cursor.execute("""
                INSERT INTO document_states (room_id, title, content)
                VALUES (%s, %s, %s)
            """, (room_id, title, content))
            
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error updating document: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('task_create')
def handle_task_create(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    title = data.get('title')
    description = data.get('description')
    status = data.get('status', 'todo')
    
    if not room_id or not title:
        return
        
    task_id = str(uuid.uuid4())
    
    # Broadcast new task to room
    emit('task_create', {
        'id': task_id,
        'room_id': room_id,
        'title': title,
        'description': description,
        'status': status,
        'created_by': current_user.id,
        'creator_username': current_user.username,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
    
    # Add to database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO project_tasks (id, room_id, title, description, status, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (task_id, room_id, title, description, status, current_user.id))
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error creating task: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('task_update')
def handle_task_update(data):
    if not current_user.is_authenticated:
        return
        
    task_id = data.get('task_id')
    room_id = data.get('room_id')
    title = data.get('title')
    description = data.get('description')
    status = data.get('status')
    
    if not task_id or not room_id:
        return
        
    # Broadcast update to room
    emit('task_update', {
        'id': task_id,
        'room_id': room_id,
        'title': title,
        'description': description,
        'status': status,
        'updated_by': current_user.id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
    
    # Update database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        update_fields = []
        params = []
        
        if title:
            update_fields.append("title = %s")
            params.append(title)
        if description:
            update_fields.append("description = %s")
            params.append(description)
        if status:
            update_fields.append("status = %s")
            params.append(status)
            
        if not update_fields:
            return
            
        params.append(task_id)
        
        query = f"""
            UPDATE project_tasks 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, params)
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error updating task: {err}")
    finally:
        cursor.close()
        conn.close()

@socketio.on('task_delete')
def handle_task_delete(data):
    if not current_user.is_authenticated:
        return
        
    task_id = data.get('task_id')
    room_id = data.get('room_id')
    
    if not task_id or not room_id:
        return
        
    # Broadcast deletion to room
    emit('task_delete', {
        'id': task_id,
        'room_id': room_id,
        'deleted_by': current_user.id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
    
    # Delete from database
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM project_tasks WHERE id = %s", (task_id,))
        conn.commit()
    except mysql.connector.Error as err:
        logger.error(f"Error deleting task: {err}")
    finally:
        cursor.close()
        conn.close()

@app.route('/messages')
@login_required
def chat_messages():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    try:
        conn = create_connection()
        if not conn:
            flash('Database connection error', 'danger')
            return redirect(url_for('collaboration_hub'))

        cursor = conn.cursor(dictionary=True)
        
        # Get total count for pagination
        cursor.execute("SELECT COUNT(*) as total FROM chat_messages WHERE user_id = %s", (current_user.id,))
        total = cursor.fetchone()['total']
        
        # Get paginated messages with correct joins and column names
        cursor.execute("""
            SELECT m.*, r.name 
            FROM chat_messages m
            LEFT JOIN collaboration_rooms r ON m.room_id = r.id
            WHERE m.user_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
        """, (current_user.id, per_page, offset))
        
        messages = cursor.fetchall()
        
        # Calculate pagination info
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page * per_page < total else None
        }
        
        return render_template('chat_messages.html', messages=messages, pagination=pagination)
        
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        flash('Error retrieving messages', 'danger')
        return redirect(url_for('collaboration_hub'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@socketio.on('join_room')
def handle_join_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    join_room(room_id)
    logger.info(f"User {current_user.id} joined room {room_id}")
    
    # Notify others in the room
    emit('user_joined', {
        'user_id': current_user.id,
        'username': current_user.username,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_id)

@socketio.on('leave_room')
def handle_leave_room(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    if not room_id:
        return
    
    leave_room(room_id)
    logger.info(f"User {current_user.id} left room {room_id}")
    
    # Notify others in the room
    emit('user_left', {
        'user_id': current_user.id,
        'username': current_user.username,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_id)

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    message = data.get('message')
    
    if not room_id or not message:
        return
        
    # Save to database first
    conn = create_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO chat_messages (room_id, user_id, message)
            VALUES (%s, %s, %s)
        """, (room_id, current_user.id, message))
        conn.commit()
        
        # Get the saved message with full details
        cursor.execute("""
            SELECT cm.id, cm.user_id, u.username, u.profile_picture, 
                   cm.message, cm.created_at
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.id = LAST_INSERT_ID()
        """)
        saved_message = cursor.fetchone()
        
        # Broadcast message to room with full details
        emit('new_message', {
            'id': saved_message['id'],
            'user_id': saved_message['user_id'],
            'username': saved_message['username'],
            'profile_picture': saved_message['profile_picture'],
            'message': saved_message['message'],
            'created_at': saved_message['created_at'].isoformat()
        }, room=room_id)
        
    except mysql.connector.Error as err:
        logger.error(f"Error saving message: {err}")
        conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@socketio.on('typing')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
        
    room_id = data.get('room_id')
    if not room_id:
        return
        
    emit('typing', {
        'user_id': current_user.id,
        'username': current_user.username
    }, room=room_id)
    

@app.route('/collaboration/<room_id>')
@login_required
def collaboration_room(room_id):
    """Render a specific collaboration room."""
    conn = create_connection()
    if not conn:
        return render_template('error.html', message="Database connection error"), 500
        
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get room info
        cursor.execute("""
            SELECT cr.*, u.username as creator_name
            FROM collaboration_rooms cr
            JOIN users u ON cr.creator_id = u.id
            WHERE cr.id = %s
        """, (room_id,))
        room = cursor.fetchone()
        
        if not room:
            return render_template(message="Room not found"), 404
            
        # Check if user has access (creator, participant, or public room)
        cursor.execute("""
            SELECT 1 FROM room_participants 
            WHERE room_id = %s AND user_id = %s
        """, (room_id, current_user.id))
        is_participant = cursor.fetchone()
        
        if not is_participant and room['is_private']:
            return render_template(message="You don't have access to this room"), 403
            
        # Get participants
        cursor.execute("""
            SELECT u.id, u.username, u.profile_picture 
            FROM room_participants rp
            JOIN users u ON rp.user_id = u.id
            WHERE rp.room_id = %s
            ORDER BY rp.last_active DESC
        """, (room_id,))
        participants = cursor.fetchall()
        
        return render_template('collaboration_room.html', 
                             room=room, 
                             participants=participants,
                             current_user_id=current_user.id)
    except mysql.connector.Error as err:
        logger.error(f"Error fetching room: {err}")
        return render_template('error.html', message="Error loading room"), 500
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def get_current_user():
    """Get the current logged-in user."""
    return current_user

@app.route('/artwork/<int:artwork_id>/report')
def report_artwork(artwork_id):
    # Get the artwork or return 404 if not found
    artwork = artwork.query.get_or_404(artwork_id)
    
    # Pass the current user if authenticated
    return render_template(
        'report_artwork.html',
        artwork=artwork,
        current_user=current_user
    )


def backup_files(filename):
    """Backup system files to a zip archive."""
    try:
        import zipfile
        backup_path = os.path.join('backups', filename)
        os.makedirs('backups', exist_ok=True)
        
        backup_items = [
            'static/uploads',
            'static/profile_pics',
            'templates',
            'config.py'
        ]
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in backup_items:
                if os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, start=os.path.dirname(item))
                            zipf.write(file_path, arcname=os.path.join(item, arcname))
                elif os.path.isfile(item):
                    zipf.write(item, arcname=item)
        
        return True
    except Exception as e:
        logging.error(f"Error backing up files: {e}")
        return False
    
def get_media_url(media_path):
    """Convert stored media paths to proper URLs"""
    if media_path.startswith(('http://', 'https://')):
        return media_path
    return url_for('static', filename=f"uploads/{os.path.basename(media_path)}")

def get_media_type(filename):
    """Determine media type based on file extension"""
    ext = filename.split('.')[-1].lower()
    if ext in {'png', 'jpg', 'jpeg', 'gif'}:
        return 'image'
    elif ext in {'mp4', 'webm', 'ogg'}:
        return 'video'
    elif ext in {'mp3', 'wav', 'ogg'}:
        return 'audio'
    return 'other'

def clear_application_cache():
    """Clear application cache."""
    try:
        from flask_caching import Cache
        cache = Cache()
        cache.clear()
        return True
    except Exception as e:
        logging.error(f"Error clearing cache: {e}")
        return False

def generate_pdf_report(data):
    """Generate PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Analytics Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(f"Date Range: {data.get('dateRange', 'N/A')}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    elements.append(Paragraph("Key Statistics", styles['Heading2']))
    stats = data.get('stats', {})
    elements.append(Paragraph(f"Total Users: {stats.get('totalUsers', 'N/A')}", styles['Normal']))
    elements.append(Paragraph(f"Total Artworks: {stats.get('totalArtworks', 'N/A')}", styles['Normal']))
    elements.append(Paragraph(f"Active Challenges: {stats.get('activeChallenges', 'N/A')}", styles['Normal']))
    elements.append(Spacer(1, 24))
    
    if data.get('includeCharts', True):
        elements.append(Paragraph("Charts", styles['Heading2']))
        
        chart_data = data.get('chartData', {})
        if chart_data.get('submissionsChart'):
            img_data = chart_data['submissionsChart'].split(',')[1]
            img = ReportLabImage(BytesIO(base64.b64decode(img_data)), width=400, height=300)
            elements.append(img)
            elements.append(Spacer(1, 12))
        
        if chart_data.get('userActivityChart'):
            img_data = chart_data['userActivityChart'].split(',')[1]
            img = ReportLabImage(BytesIO(base64.b64decode(img_data)), width=400, height=300)
            elements.append(img)
            elements.append(Spacer(1, 12))
            
        if chart_data.get('categoriesChart'):
            img_data = chart_data['categoriesChart'].split(',')[1]
            img = ReportLabImage(BytesIO(base64.b64decode(img_data)), width=300, height=300)
            elements.append(img)
            elements.append(Spacer(1, 12))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=analytics_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

def generate_csv_report(data):
    """Generate CSV report."""
    buffer = BytesIO()
    writer = csv.writer(buffer)
    
    writer.writerow(['Metric', 'Value'])
    
    stats = data.get('stats', {})
    writer.writerow(['Total Users', stats.get('totalUsers', 'N/A')])
    writer.writerow(['Total Artworks', stats.get('totalArtworks', 'N/A')])
    writer.writerow(['Active Challenges', stats.get('activeChallenges', 'N/A')])
    writer.writerow([])
    writer.writerow(['Generated on', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Date Range', data.get('dateRange', 'N/A')])
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=analytics_report_{datetime.now().strftime("%Y%m%d")}.csv'
    return response

def generate_image_report(data):
    """Generate image report."""
    chart_data = data.get('chartData', {})
    if not chart_data.get('submissionsChart'):
        return jsonify({'error': 'No chart data available'}), 400
        
    img_data = chart_data['submissionsChart'].split(',')[1]
    buffer = BytesIO(base64.b64decode(img_data))
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'attachment; filename=analytics_chart_{datetime.now().strftime("%Y%m%d")}.png'
    return response

# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="art_showcase"
    )

def get_user_data(username):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        print(f"Fetching data for username: {username}")  # Debug statement
        
        cursor.execute("SELECT username, role FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        
        print(f"User data fetched: {user_data}")  # Debug statement
        
        cursor.close()
        connection.close()
        
        return user_data
    except Exception as e:
        print(f"Error fetching user data: {e}")  # Debug statement
        return None
    
def get_leaderboard():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        leaderboard_data = cursor.fetchall()
        return leaderboard_data
    except mysql.connector.Error as e:
        print(f"Error fetching leaderboard data: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# =============================================
# MODELS
# =============================================

class Users(UserMixin):
    """User model for authentication."""
    def __init__(self, id, username, password, first_name=None, last_name=None, 
                 phone=None, role=None, address=None, email=None, points=0, 
                 badges="", bio=None, profile_picture=None,is_admin=False, **kwargs):
        self.id = id
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.role = role
        self.address = address
        self.email = email
        self.points = points
        self.badges = badges
        self.bio = bio
        self.profile_picture = profile_picture
        self.is_admin = is_admin

# =============================================
# FLASK-LOGIN CONFIGURATION
# =============================================

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return Users(**user_data)
    return None

# =============================================
# ROUTES - AUTHENTICATION
# =============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    error = None
    
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = create_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()

            if user_data:
                if check_password_hash(user_data['password'], password):
                    user = Users(**user_data)
                    login_user(user)
                    
                    if username in ["smuggerteey", "cicada403"]:
                        return redirect(url_for('admindashboard'))
                    elif user_data['role'] == 'Artist':
                        return redirect(url_for('dashboard'))
                    elif user_data['role'] == 'Regular User':
                        return redirect(url_for('userdashboard'))
                    else:
                        error = "Invalid role! Contact admin."
                else:
                    error = "Invalid username or password"
            else:
                error = "Invalid username or password"
        
        except mysql.connector.Error as e:
            logging.error(f"Database error: {e}")
            error = "There was an error processing your request. Please try again."

    return render_template('login.html', error=error)

@app.route('/check-username')
def check_username():
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False})
    
    try:
        conn = create_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
            user = cursor.fetchone()
        return jsonify({'available': user is None})
    except Exception as e:
        print(f"Error checking username: {e}")
        return jsonify({'available': False}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        # Get form data
        username = request.form.get("username", "").strip()
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip()
        address = request.form.get("address", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirmPassword", "").strip()

        # Validate required fields
        if not all([username, first_name, last_name, phone, role, address, email, password]):
            flash("❌ All fields are required!", "error")
            return redirect(url_for("registration"))

        # Validate password match
        if password != confirm_password:
            flash("❌ Passwords do not match!", "error")
            return redirect(url_for("registration"))

        # Validate location
        if len(address) < 3:
            flash("❌ Location must be at least 3 characters", "error")
            return redirect(url_for("registration"))
        
        if re.match(r'^[0-9\s]+$', address):
            flash("❌ Location cannot be just numbers", "error")
            return redirect(url_for("registration"))

        # Validate email format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("❌ Invalid email format", "error")
            return redirect(url_for("registration"))

        # Check username availability again (race condition protection)
        conn = None
        try:
            conn = create_connection()
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash("❌ Username is already taken", "error")
                    return redirect(url_for("registration"))

                # Hash password only after all validations pass
                hashed_password = generate_password_hash(password)

                # Insert user
                cursor.execute("""
                    INSERT INTO Users (username, first_name, last_name, phone, role, address, email, password)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (username, first_name, last_name, phone, role, address, email, hashed_password))
                
                conn.commit()

                # Handle redirection based on role
                if role == "Artist":
                    flash("✅ Registration successful! Please complete artist verification", "success")
                    return redirect(url_for("artist_verification", username=username))
                else:
                    flash("✅ Registration successful! Please login", "success")
                    return redirect(url_for("login"))

        except pymysql.MySQLError as e:
            if conn:
                conn.rollback()
            flash(f"❌ Database Error: {str(e)}", "error")
            return redirect(url_for("registration"))
        finally:
            if conn:
                conn.close()

    return render_template('registration.html')

@app.route('/artist-verification/<username>', methods=['GET', 'POST'])
def artist_verification(username):
    conn = create_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        artist_type = request.form.get('artistType')
        security_answer1 = request.form.get('securityAnswer1')
        security_answer2 = request.form.get('securityAnswer2')

        # ✅ Define pre-set security questions
        security_question1 = "What is the name of your first school?"
        security_question2 = "What is your favorite artist or artwork?"

        try:
            # ✅ Check if user exists in Users table
            cursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                flash("❌ Error: User does not exist. Please register first.", "error")
                return redirect(url_for("registration"))

            # ✅ Insert into ArtistVerification table
            cursor.execute("""
                INSERT INTO ArtistVerification (username, artist_type, security_question1, security_answer1, security_question2, security_answer2, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
            """, (username, artist_type, security_question1, security_answer1, security_question2, security_answer2))

            conn.commit()
            flash("✅ Artist verification submitted! Await admin approval.", "success")
            return redirect(url_for("dashboard"))

        except pymysql.MySQLError as e:
            conn.rollback()
            flash(f"❌ Error: {str(e)}", "error")
            return redirect(url_for("artist_verification", username=username))

        finally:
            cursor.close()
            conn.close()

    return render_template('verification.html', username=username)

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('home'))

# =============================================
# ROUTES - CORE FUNCTIONALITY
# =============================================

@app.route('/')
def home():
    """Home page route."""
    user_data = {
        'username': 'example_user',
        'role': 'Artist'
    }
    return render_template('index.html', user_data=user_data)

@app.route('/virtual_gallery')
def virtual_gallery():
    """Display all media in a gallery"""
    try:
        # Get artworks
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, title, description, media, 
                   DATE_FORMAT(created_at, '%Y-%m-%d') as upload_date
            FROM artwork
            ORDER BY created_at DESC
        """)
        artworks = cursor.fetchall()
        
        # Enhance artworks with media info
        for artwork in artworks:
            artwork['media_url'] = get_media_url(artwork['media'])
            artwork['media_type'] = get_media_type(artwork['media'])
        
        # Get user data if logged in
        user_data = None
        username = session.get('username')
        
        if username:
            # Get complete user data in a single query
            cursor.execute("""
                SELECT username, role, email, profile_pic 
                FROM users 
                WHERE username = %s
            """, (username,))
            user_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('gallery.html', 
                             artworks=artworks,
                             user =current_user,
                             username=username,
                             user_data=user_data,
                             current_year=datetime.now().year)
    
    except Exception as e:
        # Ensure connections are closed even if error occurs
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return f"Error fetching artworks: {str(e)}", 500

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files from upload directory"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/artwork/<int:artwork_id>')
def view_artwork(artwork_id):
    """View detailed artwork with proper media player and related artworks"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get main artwork details
        cursor.execute("""
            SELECT a.*, u.username as artist_name
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (artwork_id,))
        artwork = cursor.fetchone()
        
        if not artwork:
            cursor.close()
            conn.close()
            return "Artwork not found", 404
            
        # Determine media type and URL
        artwork['media_url'] = get_media_url(artwork['media'])
        artwork['media_type'] = get_media_type(artwork['media'])
        
        # Get 4 related artworks from the same artist (excluding current artwork)
        cursor.execute("""
            SELECT a.id, a.title, a.media, a.price
            FROM artwork a
            WHERE a.user_id = %s AND a.id != %s
            ORDER BY a.created_at DESC
            LIMIT 4
        """, (artwork['user_id'], artwork_id))
        
        related_artworks = []
        for row in cursor.fetchall():
            row['media_url'] = get_media_url(row['media'])
            row['media_type'] = get_media_type(row['media'])
            related_artworks.append(row)
        
        cursor.close()
        conn.close()
        
        # Get user data if logged in
        user_data = None
        if 'username' in session:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (session['username'],))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
        
        return render_template(
            'artwork_detail.html',
            artwork=artwork,
            user = current_user,
            related_artworks=related_artworks,
            user_data=user_data,
            username=session.get('username')
        )
    
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return f"Error fetching artwork: {str(e)}", 500
from datetime import datetime

def datetimeformat(value, format='%b %d, %Y %I:%M %p'):
    if value is None:
        return ""
    return value.strftime(format)

# Add this to your Flask app creation
app.jinja_env.filters['datetimeformat'] = datetimeformat

@app.route('/dashboard')
@login_required
def dashboard():
    """Artist dashboard."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch challenges
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()

    # Calculate stats
    cursor.execute("SELECT COUNT(*) AS total_artworks FROM artwork WHERE user_id = %s", (current_user.id,))
    total_artworks = cursor.fetchone()['total_artworks']

    # Use backticks around `Like`
    cursor.execute("SELECT COUNT(*) AS total_likes FROM `Like` WHERE artwork_id IN (SELECT id FROM artwork WHERE user_id = %s)", (current_user.id,))
    total_likes = cursor.fetchone()['total_likes']

    cursor.execute("""
    SELECT COUNT(DISTINCT id) as collector_count 
    FROM purchases
    WHERE artwork_id IN (
        SELECT id 
        FROM artwork 
        WHERE user_id = %s
    )
""", (current_user.id,))
    collector_count = cursor.fetchone()['collector_count']

    cursor.execute("SELECT COUNT(*) AS total_views FROM Views WHERE artwork_id IN (SELECT id FROM artwork WHERE user_id = %s)", (current_user.id,))
    total_views = cursor.fetchone()['total_views']

    cursor.execute("SELECT SUM(price) AS total_earnings FROM Purchases WHERE artwork_id IN (SELECT id FROM artwork WHERE user_id = %s)", (current_user.id,))
    total_earnings = cursor.fetchone()['total_earnings'] or 0.0

    cursor.close()
    conn.close()

    return render_template('dashboard.html', 
                           challenges=challenges, 
                           user=current_user, 
                           total_artworks=total_artworks, 
                           total_likes=total_likes, 
                           total_views=total_views,
                           collector_count=collector_count, 
                           total_earnings=total_earnings)

from datetime import datetime

def format_datetime(value, format='%b %d, %Y %I:%M %p'):
    """Format a datetime object or string."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

# Register the filter
app.jinja_env.filters['datetimeformat'] = format_datetime

@app.route('/userdashboard')
@login_required
def userdashboard():
    """Regular user dashboard with dynamic data."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user statistics - using backticks for reserved keywords
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM challenges WHERE id = %s) AS challenges_participated,
                (SELECT COUNT(*) FROM `like` WHERE artwork_id IN 
                    (SELECT id FROM artwork WHERE user_id = %s)) AS likes_received,
                (SELECT COUNT(*) FROM purchases WHERE buyer_id = %s) AS purchases_made,
                (SELECT COUNT(*) FROM messages WHERE recipient_id = %s AND read_status = 0) AS unread_messages
        """, (current_user.id, current_user.id, current_user.id, current_user.id))
        stats = cursor.fetchone() or {}
        
        # Get leaderboard score
        cursor.execute("SELECT score FROM leaderboard WHERE id = %s", (current_user.id,))
        leaderboard_data = cursor.fetchone()
        leaderboard_score = leaderboard_data['score'] if leaderboard_data else 0
        
        # Get recent activity
        cursor.execute("""
            SELECT * FROM user_interactions 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 4
        """, (current_user.id,))
        recent_activity = cursor.fetchall()
        
        # Get recent artworks
        cursor.execute("""
            SELECT * FROM artwork 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 3
        """, (current_user.id,))
        recent_artworks = cursor.fetchall()
        
        # Get ongoing challenges
        cursor.execute("""
            SELECT c.*, uc.progress 
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.id = %s AND c.deadline > NOW()
            ORDER BY c.deadline ASC
            LIMIT 2
        """, (current_user.id,))
        ongoing_challenges = cursor.fetchall()
        
        return render_template('userdashboard.html',
                            user=current_user,
                            stats={
                                'leaderboard_score': leaderboard_score,
                                'challenges_participated': stats.get('challenges_participated', 0),
                                'purchases_made': stats.get('purchases_made', 0),
                                'unread_messages': stats.get('unread_messages', 0),
                                'likes_received': stats.get('likes_received', 0)
                            },
                            recent_activity=recent_activity,
                            recent_artworks=recent_artworks,
                            ongoing_challenges=ongoing_challenges)
    
    except Exception as e:
        print(f"Database error: {e}")
        # Return empty/default data if there's an error
        return render_template('userdashboard.html',
                            user=current_user,
                            stats={
                                'leaderboard_score': 0,
                                'challenges_participated': 0,
                                'purchases_made': 0,
                                'unread_messages': 0,
                                'likes_received': 0
                            },
                            recent_activity=[],
                            recent_artworks=[],
                            ongoing_challenges=[])
    
    finally:
        cursor.close()
        conn.close()

@app.route('/admindashboard')
@login_required
def admindashboard():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admindashboard.html', challenges=challenges, user=current_user)

@app.route('/sketchboard')
@login_required
def sketchboard():
    """Sketchboard page."""
    try:
        user_data = get_user_data(current_user.username)
        leaderboard_data = get_leaderboard()
        
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Challenges")
        challenges = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('sketchboard.html', 
                             user_data=user_data,
                             user = current_user, 
                             leaderboard_data=leaderboard_data, 
                             challenges=challenges)
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/update_points', methods=['POST'])
def update_points():
    data = request.get_json()
    username = data.get('username')
    points = data.get('points')

    if not username or not points:
        return jsonify({'error': 'Missing username or points'}), 400

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Check if the user already has a score entry
        cursor.execute("SELECT score FROM leaderboard WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            # Update existing score
            new_score = result[0] + points
            cursor.execute("UPDATE leaderboard SET score = %s WHERE username = %s", (new_score, username))
        else:
            # Insert new score entry
            cursor.execute("INSERT INTO leaderboard (username, score) VALUES (%s, %s)", (username, points))

        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/submit_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def submit_challenge(challenge_id):
    """Submit a challenge."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges WHERE id = %s", (challenge_id,))
    challenge = cursor.fetchone()

    if challenge:
        cursor.execute("UPDATE Users SET points = points + %s WHERE id = %s", 
                      (challenge['points_reward'], current_user.id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    return "Challenge not found!", 404

@app.route('/create_challenges', methods=['GET', 'POST'])
@login_required
def create_challenges():
    """Create new challenges."""
    if request.method == 'POST':
        name = request.form.get("name")
        description = request.form.get("description")
        deadline = request.form.get("deadline")
        points_reward = request.form.get("points_reward", type=int)

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO challenges (name, description, deadline, points_reward)
                VALUES (%s, %s, %s, %s)
            """, (name, description, deadline, points_reward))
            conn.commit()
        except mysql.connector.Error as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return "There was an error creating the challenge.", 500
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('display_challenges'))

    return render_template('create_challenges.html', user =current_user)

@app.route('/edit_challenge', methods=['POST'])
def edit_challenge():
    challenge_id = request.form['id']
    name = request.form['name']
    description = request.form['description']
    deadline = request.form['deadline']
    points_reward = request.form['points_reward']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE challenges SET name=%s, description=%s, deadline=%s, points_reward=%s WHERE id=%s",
                   (name, description, deadline, points_reward, challenge_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('display_challenges'))

@app.route('/delete_challenge', methods=['POST'])
def delete_challenge():
    challenge_id = request.form['id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM challenges WHERE id=%s", (challenge_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('display_challenges'))

@app.route('/display_challenges')
@login_required
def display_challenges():
    """Display all challenges."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('display.html', 
                         challenges=challenges, 
                         user=user, 
                         username=username, 
                         user_data=user_data)

@app.route('/leaderboard')
@login_required
def leaderboard():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        print("Fetching leaderboard data...")  # Debug statement
        
        cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        leaderboard_data = cursor.fetchall()
        
        print(f"Leaderboard data fetched: {leaderboard_data}")  # Debug statement
        
        cursor.close()
        connection.close()
        
        return render_template('leaderboard.html', leaderboard_data=leaderboard_data,user =current_user)
    except Exception as e:
        print(f"Error fetching leaderboard data: {e}")  # Debug statement
        flash('An error occurred while fetching the leaderboard.', 'error')
        return redirect(url_for('leaderboard'))  # Redirect to a safe page
    
@app.route('/get_statistics')
@login_required
def get_statistics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch total users
        cursor.execute("SELECT COUNT(*) AS total_users FROM Users")
        total_users = cursor.fetchone()['total_users']

        # Fetch total artwork submissions
        cursor.execute("SELECT COUNT(*) AS total_artwork FROM Artwork")
        total_artwork = cursor.fetchone()['total_artwork']

        # Fetch active projects (e.g., challenges with a deadline in the future)
        cursor.execute("SELECT COUNT(*) AS active_projects FROM Challenges WHERE deadline > %s", (datetime.utcnow(),))
        active_projects = cursor.fetchone()['active_projects']

        cursor.close()
        conn.close()

        # Return the statistics as JSON
        return jsonify({
            'total_users': total_users,
            'total_artwork': total_artwork,
            'active_projects': active_projects
        })
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500
    
@app.route('/get_recent_submissions')
@login_required
def get_recent_submissions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch recent submissions with dates
        cursor.execute("""
            SELECT Artwork.title, Users.username, Artwork.created_at 
            FROM Artwork 
            JOIN Users ON Artwork.user_id = Users.id 
            ORDER BY Artwork.created_at DESC 
            LIMIT 5
        """)
        recent_submissions = cursor.fetchall()

        cursor.close()
        conn.close()

        # Format the dates for better readability
        for submission in recent_submissions:
            submission['created_at'] = submission['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(recent_submissions)
    except Exception as e:
        print(f"Error fetching recent submissions: {e}")
        return jsonify({'error': 'Failed to fetch recent submissions'}), 500
@app.route('/get_users')
@login_required
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch all users
        cursor.execute("SELECT id, username, email, role FROM Users")
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(users)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500
    
@app.route('/remove_user/<int:user_id>', methods=['DELETE'])
@login_required
def remove_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Delete the user
        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error removing user: {e}")
        return jsonify({'error': 'Failed to remove user'}), 500

# =============================================
# ROUTES - ARTWORK MANAGEMENT
# =============================================
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_artwork():
    if request.method == 'POST':
        # Get form data
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "0").strip()
        tags = request.form.get("tags", "").strip()
        media = request.files.get("media")
        category = request.form.get("category", "").strip()
        force_upload = request.form.get("force_upload", "false").lower() == "true"

        # Validate required fields
        if not all([title, description, price, tags, media, category]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields'
            }), 400

        try:
            price = float(price)
            if price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid price'
            }), 400


        # Calculate file hash
        file_content = media.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        media.seek(0)  # Reset file pointer

        conn = create_connection()
        if conn is None:
            return jsonify({
                'success': False,
                'message': 'Database connection error'
            }), 500
            
        cursor = conn.cursor(dictionary=True)

        try:
            # Check for duplicate artwork
            cursor.execute("""
                SELECT a.id, a.title, a.user_id, a.duplicate_count, u.username
                FROM artwork a
                JOIN users u ON a.user_id = u.id
                WHERE a.file_hash = %s 
                ORDER BY a.created_at ASC 
                LIMIT 1
            """, (file_hash,))
            existing_art = cursor.fetchone()

            if existing_art and not force_upload:
                return jsonify({
                    'success': False,
                    'is_duplicate': True,
                    'message': f'This artwork was already uploaded by {existing_art["username"]}.',
                    'original_owner': existing_art["username"],
                    'original_title': existing_art["title"],
                    'duplicate_count': existing_art["duplicate_count"]
                }), 409

            # Save the file
            filename = secure_filename(media.filename)
            file_path = os.path.join("static/uploads", filename)
            
            # Ensure unique filename
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                file_path = os.path.join("static/uploads", f"{name}_{counter}{ext}")
                counter += 1
            
            media.save(file_path)

            # Calculate perceptual hash for images
            perceptual_hash = None
            if media.content_type.startswith('image'):
                try:
                    img = Image.open(media.stream)
                    perceptual_hash = str(imagehash.average_hash(img))
                    media.seek(0)
                except Exception as e:
                    logging.error(f"Image processing error: {e}")

            # Determine if this needs review
            needs_review = False
            original_upload_id = None
            duplicate_count = 0
            
            if existing_art:
                original_upload_id = existing_art['id']
                duplicate_count = existing_art['duplicate_count'] + 1
                needs_review = duplicate_count >= 2
                
                # Update duplicate count on original
                cursor.execute("""
                    UPDATE artwork 
                    SET duplicate_count = duplicate_count + 1 
                    WHERE id = %s
                """, (original_upload_id,))

            # Insert new artwork
            cursor.execute("""
                INSERT INTO artwork (
                    title, description, price, tags, media, user_id, 
                    file_hash, perceptual_hash, category, original_upload_id, 
                    duplicate_count, needs_admin_review, is_approved
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                title, description, price, tags, file_path, 
                current_user.id, file_hash, perceptual_hash, category, original_upload_id,
                duplicate_count, needs_review, not needs_review
            ))
            
            artwork_id = cursor.lastrowid
            
            # Add "second-hand" tag if this is a duplicate
            if original_upload_id:
                cursor.execute("""
                    UPDATE artwork 
                    SET tags = CONCAT(tags, ', second-hand') 
                    WHERE id = %s
                """, (artwork_id,))
            
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Artwork uploaded successfully!',
                'needs_review': needs_review,
                'artwork_id': artwork_id
            })

        except Exception as e:
            conn.rollback()
            logging.error(f"Upload error: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': 'Error uploading artwork'
            }), 500
        finally:
            cursor.close()
            conn.close()

    return render_template("upload_artwork.html", user=current_user)

@app.route('/admin/review')
@login_required
def admin_review():
    return render_template("admin_review.html",user=current_user)

@app.route('/api/artworks_needing_review')
@login_required
def artworks_needing_review():
    conn = create_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch both artworks needing review AND all duplicates
        cursor.execute("""
            SELECT a.*, u.username as owner_username 
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.needs_admin_review = TRUE 
               OR a.original_upload_id IS NOT NULL
               OR a.duplicate_count > 0
            ORDER BY 
                CASE 
                    WHEN a.needs_admin_review = TRUE THEN 0
                    WHEN a.original_upload_id IS NOT NULL THEN 1
                    ELSE 2
                END,
                a.created_at DESC
        """)
        artworks = cursor.fetchall()
        
        # Enhance the data with duplicate information
        enhanced_artworks = []
        for artwork in artworks:
            if artwork['original_upload_id']:
                cursor.execute("""
                    SELECT title, user_id 
                    FROM artwork 
                    WHERE id = %s
                """, (artwork['original_upload_id'],))
                original = cursor.fetchone()
                if original:
                    cursor.execute("""
                        SELECT username 
                        FROM users 
                        WHERE id = %s
                    """, (original['user_id'],))
                    original_owner = cursor.fetchone()
                    artwork['original_title'] = original['title']
                    artwork['original_owner'] = original_owner['username'] if original_owner else 'Unknown'
            
            enhanced_artworks.append(artwork)
        
        return jsonify(enhanced_artworks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/review_artwork', methods=['POST'])
@login_required
def review_artwork():
    artwork_id = request.form.get('artwork_id')
    action = request.form.get('action')
    
    if not artwork_id or not action:
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400
    
    conn = create_connection()
    if conn is None:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        if action == 'approve':
            # For duplicates, we might want to keep track of approved duplicates
            cursor.execute("""
                UPDATE artwork 
                SET is_approved = TRUE, 
                    needs_admin_review = FALSE,
                    is_approved = 1
                WHERE id = %s
            """, (artwork_id,))
            message = 'Artwork approved successfully'
        else:
            # For duplicates, we might want to reject all copies
            cursor.execute("""
                SELECT media, original_upload_id 
                FROM artwork 
                WHERE id = %s
            """, (artwork_id,))
            artwork_data = cursor.fetchone()
            file_path = artwork_data['media']
            
            if artwork_data['original_upload_id']:
                # If this is a duplicate, we might want to reject all copies
                cursor.execute("""
                    DELETE FROM artwork 
                    WHERE original_upload_id = %s OR id = %s
                """, (artwork_data['original_upload_id'], artwork_id))
            else:
                cursor.execute("DELETE FROM artwork WHERE id = %s", (artwork_id,))
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error deleting file: {e}")
            message = 'Artwork rejected and removed'
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/marketplace')
def marketplace():
    """Artwork marketplace."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role, 'id': user.id}
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch artworks
    cursor.execute("""
        SELECT 
            a.*,
            u.username as artist,
            u.id as artist_id
        FROM artwork a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.category, a.created_at DESC
    """)
    artworks = cursor.fetchall()

    # Enhance artworks with media info
    for artwork in artworks:
        artwork['media_url'] = get_media_url(artwork['media'])
        artwork['media_type'] = get_media_type(artwork['media'])

    # Organize artworks by category
    artworks_by_category = {}
    for artwork in artworks:
        category = artwork['category']
        if category not in artworks_by_category:
            artworks_by_category[category] = []
        artworks_by_category[category].append(artwork)

    # Fetch statistics
    cursor.execute("SELECT COUNT(*) as count FROM artwork")
    artwork_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'Artist'")
    artist_count = cursor.fetchone()['count']

    cursor.execute("""
        SELECT COUNT(DISTINCT id) as count 
        FROM purchases
    """)
    collector_count = cursor.fetchone()['count']

    # Hard-coded country count
    country_count = 54  # This can be adjusted as needed

    cursor.close()
    conn.close()
    
    return render_template('marketplace.html', 
                         artworks_by_category=artworks_by_category,
                         user=user, 
                         username=username, 
                         user_data=user_data,
                         artwork_count=artwork_count,
                         artist_count=artist_count,
                         collector_count=collector_count,
                         country_count=country_count)

@app.route('/delete_artwork', methods=['DELETE'])
def delete_artwork():
    """Delete artwork."""
    artwork_id = request.args.get('id')
    
    if not artwork_id:
        return jsonify({'success': False, 'error': 'No ID provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM artwork WHERE id = %s", (artwork_id,))
        conn.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/reports')
@login_required
def admin_reports():
    # Get all reports from the database
    return render_template('admin_reports.html', user=current_user)


# =============================================
# ROUTES - USER PROFILE
# =============================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    user = get_current_user()
    artworks = []
    
    # Database connection for fetching artworks and extended user data
    conn = create_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Fetch user's artworks with comprehensive path handling
            cursor.execute("""
                SELECT 
                    id,
                    title,
                    description,
                    price,
                    tags,
                    created_at,
                    CASE 
                        WHEN media LIKE 'http%' THEN media
                        WHEN media LIKE 'static/%' THEN media
                        WHEN media LIKE 'profile_pics/%' THEN CONCAT('static/', media)
                        ELSE CONCAT('static/uploads/', media)
                    END AS media_path,
                    user_id
                FROM artwork
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user.id,))
            artworks = cursor.fetchall()
            
            # Fetch complete user data including new fields
            cursor.execute("""
                SELECT 
                    id, username, email, first_name, last_name, bio, 
                    profile_picture, role, phone, address, created_at, status
                FROM Users 
                WHERE id = %s
            """, (user.id,))
            user_data = cursor.fetchone()
            if user_data:
                user = type('User', (), user_data)  # Convert dict to object for template compatibility
            
            app.logger.debug(f"Fetched user data: {user_data}")

    except mysql.connector.Error as err:
        flash('Error fetching profile data', 'error')
        app.logger.error(f"Database error: {err}")
    finally:
        conn.close()

    if request.method == 'POST':
        # Process form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        bio = request.form.get('bio')
        phone = request.form.get('phone')
        address = request.form.get('address')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        profile_picture = request.files.get('profile_picture')

        conn = create_connection()
        try:
            with conn.cursor() as cursor:
                updates = []
                params = []
                
                # Basic info updates
                if first_name != user.first_name:
                    updates.append("first_name = %s")
                    params.append(first_name)
                if last_name != user.last_name:
                    updates.append("last_name = %s")
                    params.append(last_name)
                if bio != user.bio:
                    updates.append("bio = %s")
                    params.append(bio)
                if phone != user.phone:
                    updates.append("phone = %s")
                    params.append(phone)
                if address != user.address:
                    updates.append("address = %s")
                    params.append(address)
                
                # Password change handling
                if current_password and new_password and confirm_password:
                    if new_password != confirm_password:
                        flash('New passwords do not match', 'error')
                    else:
                        # Verify current password
                        cursor.execute("SELECT password FROM Users WHERE id = %s", (user.id,))
                        result = cursor.fetchone()
                        if result and check_password_hash(result[0], current_password):
                            updates.append("password = %s")
                            params.append(generate_password_hash(new_password))
                            flash('Password updated successfully!', 'success')
                        else:
                            flash('Current password is incorrect', 'error')
                
                # Handle profile picture upload
                if profile_picture and profile_picture.filename:
                    if not allowed_file(profile_picture.filename):
                        flash('Invalid file type. Only PNG, JPG, JPEG, GIF allowed.', 'error')
                    else:
                        # Create upload directory if it doesn't exist
                        os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)
                        
                        # Delete old profile picture if exists
                        if user.profile_picture and user.profile_picture != 'static/default_profile.png':
                            old_pic_path = os.path.join(app.root_path, user.profile_picture)
                            if os.path.exists(old_pic_path):
                                try:
                                    os.remove(old_pic_path)
                                except Exception as e:
                                    app.logger.error(f"Error deleting old profile picture: {e}")
                        
                        # Save new profile picture
                        ext = os.path.splitext(profile_picture.filename)[1].lower()
                        filename = f"user_{user.id}_{int(time.time())}{ext}"
                        filename = secure_filename(filename)
                        save_path = os.path.join(app.config['PROFILE_PICS_FOLDER'], filename)
                        
                        profile_picture.save(save_path)
                        
                        # Store relative path in database
                        db_path = os.path.join('profile_pics', filename).replace('\\', '/')
                        updates.append("profile_picture = %s")
                        params.append(db_path)
                        
                        flash('Profile picture updated successfully!', 'success')
                
                # Only update if there are changes
                if updates:
                    update_query = "UPDATE Users SET " + ", ".join(updates) + " WHERE id = %s"
                    params.append(user.id)
                    cursor.execute(update_query, tuple(params))
                    conn.commit()
                    flash('Profile updated successfully!', 'success')
                else:
                    flash('No changes detected', 'info')
                
                # Refresh user data
                user = get_current_user()
                return redirect(url_for('profile'))
            
        except Exception as e:
            conn.rollback()
            flash('Error updating profile: ' + str(e), 'error')
            app.logger.error(f"Profile update error: {e}")
        finally:
            conn.close()

    return render_template('profile.html', 
                         user=user,
                         artworks=artworks,
                         username=user.username)

# =============================================
# ROUTES - PAYMENTS
# =============================================

@app.route('/checkout/<int:artwork_id>', methods=['GET'])
def checkout(artwork_id):
    user = get_current_user()
    user_data = {'role': user.role} 
    if not user:
        flash('Please login to complete your purchase', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get artwork details
        cursor.execute("""
            SELECT a.*, u.username as artist,
                       u.id as artist_id 
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (artwork_id,))
        artwork = cursor.fetchone()

        if not artwork:
            flash('Artwork not found', 'error')
            return redirect(url_for('marketplace'))

        # Prevent self-purchase
        if user.id == artwork['artist_id']:
            flash("You cannot purchase your own artwork", 'error')
            return redirect(url_for('marketplace'))

        return render_template('checkout.html', artwork=artwork, user=current_user, user_data=user_data)

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('marketplace'))
    finally:
        cursor.close()
        conn.close()


from decimal import Decimal

@app.route('/receipt/<receipt_number>')
def view_receipt(receipt_number):
    user = get_current_user()
    user_data = {'role': user.role} 
    if not user:
        flash('Please login to view your receipt', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*, p.*, a.title as artwork_title, a.price, 
               u1.username as buyer_name, u2.username as artist_name
        FROM receipts r
        JOIN purchases p ON r.purchase_id = p.id
        JOIN artwork a ON p.artwork_id = a.id
        JOIN users u1 ON p.buyer_id = u1.id
        JOIN users u2 ON a.user_id = u2.id
        WHERE r.receipt_number = %s AND p.buyer_id = %s
    """, (receipt_number, user.id))
    
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()

    if not receipt:
        flash('Receipt not found', 'error')
        return redirect(url_for('marketplace'))

    # Convert Decimal to float and calculate values
    price = float(Decimal(str(receipt['price'])))
    receipt['subtotal'] = price
    receipt['fee'] = price * 0.15
    receipt['total'] = price * 1.15

    return render_template('receipt.html', receipt=receipt, user = current_user, user_data=user_data)

from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

@app.route('/receipt/<receipt_number>.png')
def download_receipt(receipt_number):
    user = get_current_user()
    if not user:
        flash('Please login to view your receipt', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*, p.*, a.title as artwork_title, a.price, 
               u1.username as buyer_name, u2.username as artist_name
        FROM receipts r
        JOIN purchases p ON r.purchase_id = p.id
        JOIN artwork a ON p.artwork_id = a.id
        JOIN users u1 ON p.buyer_id = u1.id
        JOIN users u2 ON a.user_id = u2.id
        WHERE r.receipt_number = %s AND p.buyer_id = %s
    """, (receipt_number, user.id))
    
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()

    if not receipt:
        flash('Receipt not found', 'error')
        return redirect(url_for('marketplace'))

    # Create receipt image
    img = generate_receipt_image(receipt)
    
    # Create response
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png', download_name=f'receipt_{receipt_number}.png')

def generate_receipt_image(receipt):
    # Create blank image
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 30)
        header_font = ImageFont.truetype("arialbd.ttf", 22)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Draw header
    draw.text((width//2, 50), "Africcase", fill=(6, 187, 204), font=title_font, anchor="mm")
    draw.text((width//2, 90), "RECEIPT", fill=(0, 0, 0), font=header_font, anchor="mm")
    draw.text((width//2, 130), f"#{receipt['receipt_number']}", fill=(0, 0, 0), font=header_font, anchor="mm")
    
    # Draw divider
    draw.line((50, 170, width-50, 170), fill=(200, 200, 200), width=2)
    
    # Draw receipt details
    y_position = 200
    details = [
        ("Date:", receipt['purchase_date'].strftime('%Y-%m-%d %H:%M')),
        ("Buyer:", receipt['buyer_name']),
        ("Artist:", receipt['artist_name']),
        ("Artwork:", receipt['artwork_title']),
        ("Payment Method:", receipt['payment_method'].title()),
        ("Transaction ID:", receipt['transaction_id']),
    ]
    
    for label, value in details:
        draw.text((60, y_position), label, fill=(100, 100, 100), font=text_font)
        draw.text((250, y_position), value, fill=(0, 0, 0), font=text_font)
        y_position += 40
    
    # Draw price breakdown (fixed decimal handling)
    y_position += 30
    draw.text((60, y_position), "PRICE SUMMARY", fill=(6, 187, 204), font=header_font)
    y_position += 40
    
    subtotal = float(Decimal(str(receipt['price'])))
    fee = subtotal * 0.15
    total = subtotal + fee
    
    prices = [
        ("Artwork Price:", f"${subtotal:.2f}"),
        ("Platform Fee (15%):", f"${fee:.2f}"),
        ("TOTAL:", f"${total:.2f}")
    ]
    
    for label, value in prices:
        draw.text((60, y_position), label, fill=(100, 100, 100), font=text_font)
        draw.text((width-60, y_position), value, fill=(0, 0, 0), font=text_font, anchor="rm")
        y_position += 40
    
    # Draw footer
    y_position += 50
    footer_text = "Thank you for your purchase!\nFor any questions, please contact support@creativeshowcase.com"
    for line in textwrap.wrap(footer_text, width=40):
        draw.text((width//2, y_position), line, fill=(100, 100, 100), font=text_font, anchor="mm")
        y_position += 30
    
    return img

@app.route('/purchase_history')
def purchase_history():
    user = get_current_user()
    user_data = {'role': user.role} 
    if not user:
        flash('Please login to view your purchase history', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, a.title as artwork_title, a.media, r.receipt_number
        FROM purchases p
        JOIN artwork a ON p.artwork_id = a.id
        LEFT JOIN receipts r ON r.purchase_id = p.id
        WHERE p.buyer_id = %s
        ORDER BY p.purchase_date DESC
    """, (user.id,))
    
    purchases = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('purchase_history.html', purchases=purchases,user =current_user, user_data=user_data)

@app.route('/recent/<int:artwork_id>')
def recent(artwork_id):
    user = get_current_user()
    if not user:
        flash('Please login to complete your purchase', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get artwork details with artist information
        cursor.execute("""
            SELECT a.*, u.id as artist_id, u.username as artist_name
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (artwork_id,))
        artwork = cursor.fetchone()

        if not artwork:
            flash('Artwork not found', 'error')
            return redirect(url_for('marketplace'))

        return render_template('recent.html', 
                             artwork=artwork,
                             user=user)

    except Exception as e:
        flash(f'Error loading checkout page: {str(e)}', 'error')
        return redirect(url_for('marketplace'))
    finally:
        cursor.close()
        conn.close()

@app.route('/process_purchase/<int:artwork_id>', methods=['POST'])
def process_purchase(artwork_id):
    user = get_current_user()
    if not user:
        flash('Please login to complete your purchase', 'error')
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get artwork details
        cursor.execute("""
            SELECT a.*, u.id as artist_id 
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (artwork_id,))
        artwork = cursor.fetchone()

        if not artwork:
            flash('Artwork not found', 'error')
            return redirect(url_for('marketplace'))

        # Record purchase
        cursor.execute("""
            INSERT INTO purchases 
            (buyer_id, artwork_id, price, payment_method, transaction_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user.id,
            artwork_id,
            float(Decimal(str(artwork['price']))),
            request.form.get('payment_method', 'credit_card'),
            ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        ))
        purchase_id = cursor.lastrowid

        # Generate receipt
        receipt_number = f"RCPT-{datetime.now().strftime('%Y%m%d')}-{purchase_id:06d}"
        cursor.execute("""
            INSERT INTO receipts (purchase_id, receipt_number)
            VALUES (%s, %s)
        """, (purchase_id, receipt_number))

        conn.commit()

        return redirect(url_for('view_receipt', receipt_number=receipt_number))

    except Exception as e:
        conn.rollback()
        flash(f'Purchase error: {str(e)}', 'error')
        return redirect(url_for('checkout', artwork_id=artwork_id))
    finally:
        cursor.close()
        conn.close()

@app.route('/pay', methods=['POST'])
def pay():
    """Process payment via Paystack."""
    data = request.json
    email = data.get("email")
    amount = data.get("amount")
    currency = "GHS"

    if not email or not amount:
        return jsonify({"error": "Email and amount are required"}), 400

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "amount": int(amount) * 100,
        "currency": currency
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", 
                           json=payload, 
                           headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Payment initialization failed"}), 500

@app.route('/pay/verify/<string:reference>')
def verify_payment(reference):
    """Verify Paystack payment."""
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", 
                          headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data["data"]["status"] == "success":
            return "Payment successful"
        else:
            return "Payment failed", 400
    else:
        return "Verification failed", 500

@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Process payment via PayPal."""
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    payment_method = request.form['payment_method']
    total_amount = 100.00

    if payment_method == 'paypal':
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": url_for('payment_success', _external=True),
                "cancel_url": url_for('payment_cancel', _external=True)
            },
            "transactions": [{
                "amount": {
                    "total": str(total_amount),
                    "currency": "GHS"
                },
                "description": "Purchase of artwork"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            flash('Payment creation failed. Please try again.', 'danger')
            return redirect(url_for('checkout'))

    elif payment_method == 'momo':
        flash('MoMo payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    elif payment_method == 'credit_card':
        flash('Credit card payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    else:
        flash('Invalid payment method selected.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/payment_success')
def payment_success():
    """Handle successful payment."""
    flash('Payment completed successfully! Thank you for your purchase.', 'success')
    return redirect(url_for('artworks'))

@app.route('/payment_cancel')
def payment_cancel():
    """Handle cancelled payment."""
    flash('Payment was cancelled. Please try again.', 'warning')
    return redirect(url_for('checkout'))

# =============================================
# ROUTES - ADMINISTRATION
# =============================================

def get_leaderboard():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        leaderboard_data = cursor.fetchall()
        return leaderboard_data
    except mysql.connector.Error as e:
        print(f"Error fetching leaderboard data: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# =============================================
# ROUTES - ANALYTICS AND REPORTS
# =============================================

@app.route('/insights')
@login_required
def insights():
    """Display system insights."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 5")
        leaderboard_data = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return render_template('insights.html', 
                             leaderboard_data=leaderboard_data, user= current_user)
    except Exception as e:
        logging.error(f"Error: {e}")
        return render_template('insights.html', 
                             leaderboard_data=[],
                             error=str(e))

@app.route('/export_report', methods=['POST'])
def export_report():
    """Export analytics report."""
    try:
        data = request.get_json()
        format = data.get('format', 'PDF Document').lower()
        
        if format == 'pdf document':
            return generate_pdf_report(data)
        elif format == 'csv spreadsheet':
            return generate_csv_report(data)
        elif format == 'png image':
            return generate_image_report(data)
        else:
            return jsonify({'error': 'Invalid format'}), 400
            
    except Exception as e:
        logging.error(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================
# ROUTES - MISC PAGES
# =============================================

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')


@app.route('/workshops')
def workshops():
    """Workshops page."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('workshops.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)

@app.route('/task_management')
def artwork_management():
    """Task management page."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, user_id, title, description FROM artwork")
    artworks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('task_management.html', artworks=artworks,user=current_user)

@app.route('/user_management')
def user_management():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('user_management.html', username=username, user_data=user_data, user=current_user)

# =============================================
# CHATBOT FUNCTIONALITY
# =============================================

@app.route('/chat')
def chat():
    """Chat interface."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('chat.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)


# Define chatbot model globally
MODEL_NAME = "MBZUAI/LaMini-T5-738M"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = None
chatbot_model = None

def load_model():
    global chatbot_model, tokenizer
    try:
        print("Loading chatbot model and tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        chatbot_model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
        print("Chatbot model and tokenizer loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if not data or "input_text" not in data:
        return jsonify({"error": "Invalid input. Provide 'input_text'."}), 400

    input_text = data["input_text"]
    max_length = data.get("max_length", 50)  # Default max length

    try:
        # Tokenize input
        inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True).to(device)

        # Generate response
        outputs = chatbot_model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_beams=5,
            early_stopping=True
        )

        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/artist_profiles')
def artist_profiles():
    """Display all artists or a single artist if artist_id is provided."""
    user = get_current_user()
    user_data = get_user_data(current_user.username)
    artist_id = request.args.get('artist_id')
    
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        if artist_id:
            # Get basic artist information (NEW QUERY)
            cursor.execute("""
                SELECT 
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.phone,
                    u.address,
                    u.profile_picture,
                    u.bio,
                    u.instagram,
                    u.twitter,
                    u.website
                FROM 
                    users u
                WHERE 
                    u.id = %s
            """, (artist_id,))
            artist_basic = cursor.fetchone()
            
            if not artist_basic:
                return "Artist not found", 404
                
            # Get artist statistics (existing query)
            cursor.execute("""
                SELECT 
                    COUNT(a.id) AS artwork_count,
                    IFNULL(l.score, 0) AS leaderboard_score,
                    (
                        SELECT AVG(r.rating)
                        FROM artist_ratings r
                        WHERE r.artist_id = u.id
                    ) AS average_rating,
                    (
                        SELECT COUNT(*)
                        FROM artist_ratings r
                        WHERE r.artist_id = u.id
                    ) AS rating_count,
                    (
                        SELECT COUNT(*)
                        FROM artist_followers f
                        WHERE f.artist_id = u.id
                    ) AS follower_count
                FROM 
                    users u
                LEFT JOIN 
                    artwork a ON u.id = a.user_id
                LEFT JOIN
                    leaderboard l ON u.username = l.username
                WHERE 
                    u.id = %s
                GROUP BY 
                    u.id
            """, (artist_id,))
            artist_stats = cursor.fetchone() or {}
            
            # Combine basic info and stats
            artist = {**artist_basic, **artist_stats}
                
            # Get categories for the artist
            cursor.execute("""
                SELECT DISTINCT category 
                FROM artwork 
                WHERE user_id = %s
            """, (artist_id,))
            categories = [row['category'] for row in cursor.fetchall() if row['category']]
            artist['categories'] = categories or ['Various']
            
            # Get artist's artworks with media URLs and types
            cursor.execute("""
                SELECT 
                    id, title, description, price, tags, category, 
                    media, created_at
                FROM 
                    artwork
                WHERE 
                    user_id = %s
                ORDER BY 
                    created_at DESC
            """, (artist_id,))
            
            artworks = cursor.fetchall()
            for artwork in artworks:
                artwork['media_url'] = get_media_url(artwork['media'])
                artwork['media_type'] = get_media_type(artwork['media'])
                artwork['created_at'] = artwork['created_at'].strftime('%b %d, %Y')
            
            artist['artworks'] = artworks
            
            cursor.close()
            conn.close()
            
            return render_template('single_artist_profile.html', 
                                artist=artist, 
                                user=user,
                                user_data=user_data)
            
        else:
            # Get list of all artists
            cursor.execute("""
                SELECT 
                    u.id, u.username, u.first_name, u.last_name, 
                    u.profile_picture, u.bio,
                    COUNT(a.id) AS artwork_count,
                    IFNULL(l.score, 0) AS leaderboard_score,
                    (
                        SELECT AVG(r.rating)
                        FROM artist_ratings r
                        WHERE r.artist_id = u.id
                    ) AS average_rating,
                    (
                        SELECT COUNT(*)
                        FROM artist_ratings r
                        WHERE r.artist_id = u.id
                    ) AS rating_count,
                    (
                        SELECT COUNT(*)
                        FROM artist_followers f
                        WHERE f.artist_id = u.id
                    ) AS follower_count
                FROM 
                    users u
                LEFT JOIN 
                    artwork a ON u.id = a.user_id
                LEFT JOIN
                    leaderboard l ON u.username = l.username
                WHERE 
                    u.role = 'Artist'
                GROUP BY 
                    u.id
                ORDER BY 
                    artwork_count DESC, 
                    leaderboard_score DESC,
                    average_rating DESC
            """)
            
            artists = cursor.fetchall()
            
            # Get categories for each artist
            for artist in artists:
                cursor.execute("""
                    SELECT DISTINCT category 
                    FROM artwork 
                    WHERE user_id = %s
                """, (artist['id'],))
                categories = [row['category'] for row in cursor.fetchall() if row['category']]
                artist['categories'] = categories or ['Various']
            
            cursor.close()
            conn.close()
            
            return render_template('artist_profiles.html', 
                                artists=artists, 
                                user=user,
                                user_data=user_data)
    
    except Exception as e:
        logging.error(f"Error in artist_profiles: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/artist/<int:artist_id>', methods=['GET'])
def get_artist_details(artist_id):
    """API endpoint to get detailed information about a specific artist."""
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get basic artist information (NEW QUERY)
        cursor.execute("""
            SELECT 
                u.username,
                u.first_name,
                u.last_name,
                u.email,
                u.phone,
                u.address,
                u.profile_picture,
                u.bio,
                u.instagram,
                u.twitter,
                u.website
            FROM 
                users u
            WHERE 
                u.id = %s
        """, (artist_id,))
        artist = cursor.fetchone()
        
        if not artist:
            return jsonify({'error': 'Artist not found'}), 404
            
        # Get artist statistics (existing query)
        cursor.execute("""
            SELECT 
                COUNT(a.id) AS artwork_count,
                IFNULL(l.score, 0) AS leaderboard_score,
                (
                    SELECT AVG(r.rating)
                    FROM artist_ratings r
                    WHERE r.artist_id = u.id
                ) AS average_rating,
                (
                    SELECT COUNT(*)
                    FROM artist_ratings r
                    WHERE r.artist_id = u.id
                ) AS rating_count,
                (
                    SELECT COUNT(*)
                    FROM artist_followers f
                    WHERE f.artist_id = u.id
                ) AS follower_count
            FROM 
                users u
            LEFT JOIN 
                artwork a ON u.id = a.user_id
            LEFT JOIN
                leaderboard l ON u.username = l.username
            WHERE 
                u.id = %s
            GROUP BY 
                u.id
        """, (artist_id,))
        stats = cursor.fetchone() or {}
        artist.update(stats)
        
        # Get artist's categories
        cursor.execute("""
            SELECT DISTINCT category 
            FROM artwork 
            WHERE user_id = %s
        """, (artist_id,))
        artist['categories'] = [row['category'] for row in cursor.fetchall() if row['category']]
        
        # Get artist's recent artworks (limited to 6 for featured display)
        cursor.execute("""
            SELECT 
                id, title, description, price, tags, category, 
                media, created_at
            FROM 
                artwork
            WHERE 
                user_id = %s
            ORDER BY 
                created_at DESC
            LIMIT 6
        """, (artist_id,))
        
        artworks = cursor.fetchall()
        for artwork in artworks:
            artwork['media_url'] = get_media_url(artwork['media'])
            artwork['media_type'] = get_media_type(artwork['media'])
            artwork['created_at'] = artwork['created_at'].strftime('%b %d, %Y')
        
        artist['artworks'] = artworks
        
        # Get artist's recent reviews (limited to 10)
        cursor.execute("""
            SELECT 
                r.id, r.rating, r.comment, r.created_at,
                u.username as reviewer_name,
                u.profile_picture as reviewer_avatar
            FROM 
                artist_ratings r
            JOIN 
                users u ON r.user_id = u.id
            WHERE 
                r.artist_id = %s
            ORDER BY 
                r.created_at DESC
            LIMIT 10
        """, (artist_id,))
        
        reviews = cursor.fetchall()
        for review in reviews:
            review['created_at'] = review['created_at'].strftime('%b %d, %Y')
        
        artist['reviews'] = reviews
        
        cursor.close()
        conn.close()
        
        return jsonify(artist)
        
    except Exception as e:
        logging.error(f"Error in get_artist_details: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/artist/<int:artist_id>/rate', methods=['POST'])
@login_required
def rate_artist(artist_id):
    """Rate an artist."""
    try:
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        
        if not rating or not (1 <= int(rating) <= 5):
            return jsonify({'error': 'Invalid rating'}), 400
        
        # Check if the user is rating themselves
        if current_user.id == artist_id:
            return jsonify({'error': 'You cannot rate yourself'}), 400
        
        conn = create_connection()
        cursor = conn.cursor()
        
        # Check if user already rated this artist
        cursor.execute("""
            SELECT id FROM artist_ratings 
            WHERE artist_id = %s AND user_id = %s
        """, (artist_id, current_user.id))
        
        if cursor.fetchone():
            # Update existing rating
            cursor.execute("""
                UPDATE artist_ratings
                SET rating = %s, comment = %s
                WHERE artist_id = %s AND user_id = %s
            """, (rating, comment, artist_id, current_user.id))
        else:
            # Insert new rating
            cursor.execute("""
                INSERT INTO artist_ratings (artist_id, user_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (artist_id, current_user.id, rating, comment))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error rating artist: {e}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': 'Internal server error'}), 500

# =============================================
# APPLICATION STARTUP
# =============================================

if __name__ == "__main__":
    load_model()  # Load chatbot model
    socketio.run(app, debug=True)

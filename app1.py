import re
import os
import time
import logging
import base64
import hashlib
import csv
from functools import wraps
from datetime import datetime
from io import BytesIO

from flask import (Flask, request, jsonify, render_template, redirect, send_from_directory, 
                  session, url_for, flash, make_response)
from flask_sqlalchemy import SQLAlchemy
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
import paypalrestsdk
from twilio.rest import Client
import sendgrid
from sendgrid.helpers.mail import Mail as SendGridMail, Email, To, Content
import ssl
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from web3 import Web3
from opt_einsum import contract

# =============================================
# INITIALIZATION AND CONFIGURATION
# =============================================

app = Flask(__name__)

# Configuration
app.secret_key = 'tinotenda'
app.config['UPLOAD_FOLDER'] = "static/uploads"
app.config['PROFILE_PICS_FOLDER'] = "static/profile_pics"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mp3', 'wav'}

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)

# Database configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'testDB'
}

# Third-party service configurations
TWILIO_ACCOUNT_SID = 'US153b06ac498ef1b403ab552f6673f964'
TWILIO_AUTH_TOKEN = '8PJ3VNDJV6BWD5H7VD92LSCW'
TWILIO_PHONE_NUMBER = '+2330203419613'
SENDGRID_API_KEY = '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'
PAYSTACK_SECRET_KEY = "sk_test_ed78162ac6ecfa0caadb9bc3346619e781498fb5"
MODEL_NAME = "MBZUAI/LaMini-T5-738M"

# Initialize extensions
login_manager = LoginManager(app)
socketio = SocketIO(app)
mail = Mail(app)

# =============================================
# HELPER FUNCTIONS
# =============================================

def create_connection():
    """Create a database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            logging.debug("Connected to MySQL database")
            return conn
    except mysql.connector.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def get_current_user():
    """Get the current logged-in user."""
    return current_user

def log_system_activity(user_id, activity_type, description, ip_address):
    """Log system activities for audit trail."""
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_logs (user_id, log_type, description, ip_address)
            VALUES (%s, %s, %s, %s)
        """, (user_id, activity_type, description, ip_address))
        conn.commit()
    except Exception as e:
        logging.error(f"Error logging system activity: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def send_whatsapp_message(to, message):
    """Send WhatsApp message via Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            to=f'whatsapp:{to}'
        )
        logging.info(f"WhatsApp message sent to {to}: {message.sid}")
        return True
    except Exception as e:
        logging.error(f"Failed to send WhatsApp message: {e}")
        return False

def send_email(to_email, subject, content):
    """Send email via SendGrid."""
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email("tynochagaka@gmail.com")
    to_email = To(to_email)
    content = Content("text/plain", content)
    
    context = ssl._create_unverified_context()
    
    try:
        response = sg.client.mail.send.post(request_body=mail.get(), ssl_context=context)
        logging.info(f"Email sent to {to_email}: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def backup_database(filename):
    """Backup database to a file."""
    try:
        backup_path = os.path.join('backups', filename)
        os.makedirs('backups', exist_ok=True)
        
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SHOW TABLES")
        tables = [row[f"Tables_in_{db_config['database']}"] for row in cursor.fetchall()]
        
        with open(backup_path, 'w') as f:
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE {table}")
                create_table = cursor.fetchone()
                f.write(f"{create_table['Create Table']};\n\n")
                
                cursor.execute(f"SELECT * FROM {table}")
                for row in cursor.fetchall():
                    columns = ', '.join([f"`{k}`" for k in row.keys()])
                    values = ', '.join([f"'{str(v)}'" if v is not None else 'NULL' for v in row.values()])
                    f.write(f"INSERT INTO {table} ({columns}) VALUES ({values});\n")
                f.write("\n")
        
        return True
    except Exception as e:
        logging.error(f"Error backing up database: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

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
        database="testDB"
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
                 badges="", bio=None, profile_picture=None):
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
# SOCKET.IO HANDLERS
# =============================================

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending messages via SocketIO."""
    room = data['room']
    emit('receive_message', {
        'message': data['message'],
        'username': data['username']
    }, room=room)

@socketio.on('join')
def on_join(data):
    """Handle joining rooms via SocketIO."""
    username = data['username']
    room = data['room']
    join_room(room)
    emit('receive_message', {
        'message': f'{username} has joined the room.',
        'username': 'System'
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    """Handle leaving rooms via SocketIO."""
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('receive_message', {
        'message': f'{username} has left the room.',
        'username': 'System'
    }, room=room)

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
def gallery():
    """Display all media in a gallery"""
    try:
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
        
        cursor.close()
        conn.close()
        
        return render_template('gallery.html', artworks=artworks)
    
    except Exception as e:
        return f"Error fetching artworks: {str(e)}", 500

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files from upload directory"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/artwork/<int:artwork_id>')
def view_artwork(artwork_id):
    """View detailed artwork with proper media player"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT a.*, u.username as artist_name
            FROM artwork a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        """, (artwork_id,))
        
        artwork = cursor.fetchone()
        
        if artwork:
            artwork['media_url'] = get_media_url(artwork['media'])
            artwork['media_type'] = get_media_type(artwork['media'])
        
        cursor.close()
        conn.close()
        
        if not artwork:
            return "Artwork not found", 404
            
        return render_template('artwork_detail.html', artwork=artwork)
    
    except Exception as e:
        return f"Error fetching artwork: {str(e)}", 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Artist dashboard."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', challenges=challenges, user=current_user)

@app.route('/userdashboard')
@login_required
def userdashboard():
    """Regular user dashboard."""
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('userdashboard.html', challenges=challenges, user=current_user)

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

        return redirect(url_for('dashboard'))

    return render_template('create_challenges.html')

@app.route('/display_challenges', methods=['POST'])
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

    return render_template('display.html')

@app.route('/display_challenges', methods=['POST'])
def delete_challenge():
    challenge_id = request.form['id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM challenges WHERE id=%s", (challenge_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('display.html')

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
        
        return render_template('leaderboard.html', leaderboard_data=leaderboard_data)
    except Exception as e:
        print(f"Error fetching leaderboard data: {e}")  # Debug statement
        flash('An error occurred while fetching the leaderboard.', 'error')
        return redirect(url_for('index'))  # Redirect to a safe page
    
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
    """Upload artwork."""
    if request.method == 'POST':
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        tags = request.form.get("tags")
        media = request.files.get("media")
        category = request.form.get("category")

        if not all([title, description, price, tags, media, category]):
            return jsonify({'success': False, 'message': 'Please fill in all fields and upload an artwork!'}), 400

        if media.filename == '':
            return jsonify({'success': False, 'message': 'No file selected!'}), 400

        file_hash = hashlib.sha256(media.read()).hexdigest()
        media.seek(0)

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM artwork WHERE file_hash = %s", (file_hash,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Artwork already exists!'}), 409

        filename = secure_filename(media.filename)
        file_path = os.path.join("static/uploads", filename)
        media.save(file_path)

        cursor.execute("""
            INSERT INTO artwork (title, description, price, tags, media, user_id, file_hash, category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (title, description, price, tags, file_path, current_user.id, file_hash, category))
        conn.commit()

        return jsonify({'success': True, 'message': 'Artwork uploaded successfully!'}), 200

    return render_template("upload_artwork.html")

@app.route('/api/check_artwork', methods=['POST'])
@login_required
def check_artwork():
    """Check for duplicate artwork."""
    if 'media' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    media = request.files['media']
    if media.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        file_hash = hashlib.sha256(media.read()).hexdigest()
        media.seek(0)
        
        perceptual_hash = None
        if media.content_type.startswith('image'):
            try:
                img = Image.open(media.stream)
                perceptual_hash = str(imagehash.average_hash(img))
                media.seek(0)
            except Exception as e:
                logging.error(f"Image processing error: {e}")
                return jsonify({'error': 'Error processing image'}), 400

        conn = create_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, title, user_id 
                FROM artwork 
                WHERE file_hash = %s
                LIMIT 1
            """, (file_hash,))
            exact_match = cursor.fetchone()

            if exact_match:
                return jsonify({
                    'status': 'duplicate',
                    'match_type': 'exact',
                    'existing': {
                        'id': exact_match['id'],
                        'title': exact_match['title'],
                        'is_own': exact_match['user_id'] == current_user.id
                    }
                })

            similar = []
            if perceptual_hash:
                cursor.execute("""
                    SELECT id, title, user_id 
                    FROM artwork 
                    WHERE perceptual_hash LIKE %s
                    AND user_id != %s
                    LIMIT 3
                """, (f"{perceptual_hash[:5]}%", current_user.id))
                similar = cursor.fetchall()

                if similar:
                    return jsonify({
                        'status': 'similar',
                        'matches': [{
                            'id': m['id'],
                            'title': m['title'],
                            'is_own': m['user_id'] == current_user.id
                        } for m in similar]
                    })

            return jsonify({'status': 'unique'})

        except pymysql.MySQLError as e:
            logging.error(f"Database error: {e}")
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/marketplace')
def marketplace():
    """Artwork marketplace."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role, 'id': user.id}
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
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
    
    artworks_by_category = {}
    for artwork in artworks:
        category = artwork['category']
        if category not in artworks_by_category:
            artworks_by_category[category] = []
        artworks_by_category[category].append(artwork)
    
    cursor.close()
    conn.close()
    
    return render_template('marketplace.html', 
                         artworks_by_category=artworks_by_category,
                         user=user, 
                         username=username, 
                         user_data=user_data)

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

# =============================================
# ROUTES - USER PROFILE
# =============================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    user = get_current_user()
    artworks = []
    
    # Database connection for fetching artworks
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
            
            # Debug logging
            app.logger.debug(f"Fetched {len(artworks)} artworks for user {user.id}")
            for art in artworks:
                app.logger.debug(f"Artwork {art['id']}: {art['media_path']}")

    except mysql.connector.Error as err:
        flash('Error fetching artworks', 'error')
        app.logger.error(f"Database error: {err}")
    finally:
        conn.close()

    if request.method == 'POST':
        # Process form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        bio = request.form.get('bio')
        profile_picture = request.files.get('profile_picture')

        conn = create_connection()
        try:
            with conn.cursor() as cursor:
                # Update basic profile info
                cursor.execute("""
                    UPDATE Users 
                    SET first_name = %s, last_name = %s, bio = %s 
                    WHERE id = %s
                """, (first_name, last_name, bio, user.id))

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
                        cursor.execute("""
                            UPDATE Users 
                            SET profile_picture = %s 
                            WHERE id = %s
                        """, (db_path, user.id))
                        
                        flash('Profile picture updated successfully!', 'success')
                
                conn.commit()
                flash('Profile updated successfully!', 'success')
                
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
# ROUTES - COMMUNICATION
# =============================================

@app.route('/message')
@login_required
def message():
    """Chat messaging interface."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    room = 'general'
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT username, message, timestamp 
        FROM messages 
        WHERE room = %s 
        ORDER BY timestamp ASC
    """, (room,))
    messages = cursor.fetchall()
    conn.close()
    
    return render_template('message.html', 
                         username=current_user.username, 
                         messages=messages, 
                         room=room, 
                         user_data=user_data)

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

@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
    """Send WhatsApp message."""
    data = request.json
    to = data.get('to')
    message = data.get('message')
    
    if not to or not message:
        return jsonify({'error': 'Missing "to" or "message" in request'}), 400
    
    if send_whatsapp_message(to, message):
        return jsonify({'success': 'WhatsApp message sent successfully'}), 200
    else:
        return jsonify({'error': 'Failed to send WhatsApp message'}), 500

@app.route('/send_email', methods=['POST'])
def send_email_route():
    """Send email."""
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    content = data.get('content')
    
    if not to_email or not subject or not content:
        return jsonify({'error': 'Missing "to_email", "subject", or "content" in request'}), 400
    
    if send_email(to_email, subject, content):
        return jsonify({'success': 'Email sent successfully'}), 200
    else:
        return jsonify({'error': 'Failed to send email'}), 500

# =============================================
# ROUTES - PAYMENTS
# =============================================

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

@app.route('/settings')
@login_required
def settings():
    """System settings dashboard."""
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        
        settings_data = {
            'general': {},
            'users': {},
            'content': {},
            'security': {},
            'email': {},
            'system': {}
        }
        
        cursor.execute("SELECT * FROM system_settings")
        for setting in cursor.fetchall():
            settings_data[setting['category']][setting['setting_name']] = setting['setting_value']
        
        cursor.execute("SELECT role, GROUP_CONCAT(permission) as permissions FROM role_permissions GROUP BY role")
        role_permissions = {row['role']: row['permissions'].split(',') for row in cursor.fetchall()}
        
        cursor.execute("SELECT file_type FROM allowed_file_types")
        allowed_file_types = [row['file_type'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM system_info LIMIT 1")
        system_info = cursor.fetchone() or {}
        
        cursor.execute("""
            SELECT * FROM system_logs 
            WHERE log_type IN ('SETTINGS_CHANGE', 'SYSTEM_ACTION')
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_activities = cursor.fetchall()
        
        cursor.execute("SELECT * FROM backups ORDER BY created_at DESC LIMIT 5")
        backup_history = cursor.fetchall()
        
        return render_template('settings.html',
                           user_data={
                               'username': current_user.username,
                               'role': current_user.role
                           },
                           settings=settings_data,
                           role_permissions=role_permissions,
                           allowed_file_types=allowed_file_types,
                           system_info=system_info,
                           recent_activities=recent_activities,
                           backup_history=backup_history)
    
    except Exception as e:
        logging.error(f"Error loading settings: {e}")
        flash('Failed to load system settings', 'danger')
        return redirect(url_for('admindashboard'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

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

@app.route('/api/settings/update', methods=['POST'])
@login_required
def update_settings():
    """Update system settings."""
    data = request.get_json()
    if not data or 'category' not in data or 'settings' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    
    category = data['category']
    settings = data['settings']
    
    if category not in ['general', 'users', 'content', 'security', 'email']:
        return jsonify({'error': 'Invalid settings category'}), 400
    
    conn = None
    cursor = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        conn.start_transaction()
        
        for key, value in settings.items():
            if isinstance(value, bool):
                value = '1' if value else '0'
            
            cursor.execute("""
                INSERT INTO system_settings (setting_name, setting_value, category)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (key, str(value), category))
        
        log_system_activity(
            user_id=current_user.id,
            activity_type='SETTINGS_UPDATE',
            description=f'Updated {category} settings',
            ip_address=request.remote_addr
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error updating settings: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/settings/roles', methods=['POST'])
@login_required
def update_role_permissions():
    """Update role permissions."""
    data = request.get_json()
    if not data or 'roles' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    
    conn = None
    cursor = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        conn.start_transaction()
        
        cursor.execute("DELETE FROM role_permissions")
        
        for role, permissions in data['roles'].items():
            for permission in permissions:
                cursor.execute("""
                    INSERT INTO role_permissions (role, permission)
                    VALUES (%s, %s)
                """, (role, permission))
        
        log_system_activity(
            user_id=current_user.id,
            activity_type='ROLE_UPDATE',
            description='Updated role permissions',
            ip_address=request.remote_addr
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Role permissions updated successfully'})
    
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error updating role permissions: {e}")
        return jsonify({'error': 'Failed to update role permissions'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/settings/filetypes', methods=['POST'])
@login_required
def update_file_types():
    """Update allowed file types."""
    data = request.get_json()
    if not data or 'file_types' not in data:
        return jsonify({'error': 'Invalid request format'}), 400
    
    conn = None
    cursor = None
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        conn.start_transaction()
        
        cursor.execute("DELETE FROM allowed_file_types")
        
        for file_type in data['file_types']:
            cursor.execute("""
                INSERT INTO allowed_file_types (file_type)
                VALUES (%s)
            """, (file_type,))
        
        log_system_activity(
            user_id=current_user.id,
            activity_type='SETTINGS_UPDATE',
            description='Updated allowed file types',
            ip_address=request.remote_addr
        )
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Allowed file types updated successfully'})
    
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error updating file types: {e}")
        return jsonify({'error': 'Failed to update file types'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/settings/test_email', methods=['POST'])
@login_required
def test_email_configuration():
    """Test email configuration."""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email address is required'}), 400
    
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM system_settings WHERE category = 'email'")
        email_settings = {row['setting_name']: row['setting_value'] for row in cursor.fetchall()}
        
        subject = "Test Email from System Settings"
        body = "This is a test email to verify your email configuration is working properly."
        
        if send_email(
            to_email=data['email'],
            subject=subject,
            body=body,
            smtp_host=email_settings.get('smtp_host'),
            smtp_port=email_settings.get('smtp_port'),
            smtp_username=email_settings.get('smtp_username'),
            smtp_password=email_settings.get('smtp_password'),
            use_ssl=email_settings.get('smtp_ssl') == '1',
            from_email=email_settings.get('from_email'),
            from_name=email_settings.get('from_name')
        ):
            log_system_activity(
                user_id=current_user.id,
                activity_type='EMAIL_TEST',
                description='Sent test email successfully',
                ip_address=request.remote_addr
            )
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        logging.error(f"Error testing email configuration: {e}")
        return jsonify({'error': 'Failed to test email configuration'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/settings/backup', methods=['POST'])
@login_required
def create_system_backup():
    """Create system backup."""
    data = request.get_json()
    backup_type = data.get('type', 'full')
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.zip"
        
        if backup_type == 'database':
            success = backup_database(backup_filename)
        elif backup_type == 'files':
            success = backup_files(backup_filename)
        else:
            success = backup_database(backup_filename) and backup_files(backup_filename)
        
        if success:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backups (filename, backup_type, created_by)
                VALUES (%s, %s, %s)
            """, (backup_filename, backup_type, current_user.id))
            conn.commit()
            
            cursor.execute("""
                UPDATE system_info 
                SET last_backup = NOW()
                WHERE id = 1
            """)
            conn.commit()
            
            log_system_activity(
                user_id=current_user.id,
                activity_type='BACKUP_CREATED',
                description=f'Created {backup_type} backup: {backup_filename}',
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'message': 'Backup created successfully',
                'filename': backup_filename
            })
        else:
            return jsonify({'error': 'Failed to create backup'}), 500
            
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return jsonify({'error': 'Failed to create backup'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/settings/maintenance', methods=['POST'])
@login_required
def perform_maintenance_action():
    """Perform system maintenance."""
    data = request.get_json()
    action = data.get('action')
    
    if not action:
        return jsonify({'error': 'No action specified'}), 400
    
    try:
        if action == 'clear_cache':
            clear_application_cache()
            message = 'Application cache cleared successfully'
            
        elif action == 'optimize_db':
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"OPTIMIZE TABLE {table}")
            
            message = 'Database optimization completed successfully'
            
        elif action == 'purge_logs':
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM system_logs 
                WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """)
            conn.commit()
            message = 'Purged logs older than 30 days'
            
        else:
            return jsonify({'error': 'Invalid maintenance action'}), 400
        
        log_system_activity(
            user_id=current_user.id,
            activity_type='MAINTENANCE',
            description=f'Performed maintenance: {action}',
            ip_address=request.remote_addr
        )
        
        return jsonify({'success': True, 'message': message})
    
    except Exception as e:
        logging.error(f"Error performing maintenance: {e}")
        return jsonify({'error': 'Failed to perform maintenance'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
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
                             leaderboard_data=leaderboard_data)
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

@app.route('/art_challenges')
def art_challenges():
    """Art challenges page."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('art_challenges.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)

@app.route('/collaboration_hub')
def collaboration_hub():
    """Collaboration hub page."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('collaboration_hub.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)

@app.route('/checkout')
def checkout():
    """Checkout page."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('checkout.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)

@app.route('/virtual_gallery')
def virtual_gallery():
    """Virtual gallery page."""
    user = get_current_user()
    username = user.username
    user_data = {'role': user.role} 
    return render_template('virtual_gallery.html', 
                         user=user, 
                         username=username, 
                         user_data=user_data)

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
    
    return render_template('task_management.html', artworks=artworks)

@app.route('/user_management')
def user_management():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('user_management.html', user=user, username=username, user_data=user_data)

# =============================================
# CHATBOT FUNCTIONALITY
# =============================================

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

# =============================================
# APPLICATION STARTUP
# =============================================

if __name__ == "__main__":
    load_model()  # Load chatbot model
    socketio.run(app, debug=True)
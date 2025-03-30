import hashlib
import re
import MySQLdb
from flask import Flask, request, jsonify, render_template, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector
from opt_einsum import contract
import pymysql
import requests
from werkzeug.utils import secure_filename
import torch
from flask_mail import Mail, Message #type: ignore
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from datetime import datetime
import os
from config import DATABASE_CONFIG, BLOCKCHAIN_CONFIG
from web3 import Web3
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import paypalrestsdk  

from twilio.rest import Client
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import ssl
import logging


#Ensure the profile pictures directory exists
if not os.path.exists('static/profile_pics'):
    os.makedirs('static/profile_pics')

#Initialize Flask app  
app = Flask(__name__)

#Configure Flask-Mail
mail = Mail(app)

#Set your secret key
app.secret_key = 'tinotenda'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_CONFIG['uri']

#MySQL Database Configuration
db_config = {
    'user': 'root', #Database User
    'password': '',  #Database Password
    'host': 'localhost', #Database Host
    'database': 'testDB' #Database Name
}

#Create a connection to the MySQL database
def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("Connected to MySQL database")
    except mysql.connector.Error as e:
        print(f"The error '{e}' occurred")
    return conn

def get_user_data(username):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        print(f"Fetching data for username: {username}")  #Debug statement
        
        cursor.execute("SELECT username, role FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        
        print(f"User data fetched: {user_data}")  #Debug statement
        
        cursor.close()
        connection.close()
        
        return user_data
    except Exception as e:
        print(f"Error fetching user data: {e}")  #Debug statement
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

login_manager = LoginManager()
login_manager.init_app(app)
socketio = SocketIO(app)

def get_user_id(username):
    """Fetch the user ID based on the given username."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user[0] if user else None

#Twilio Configuration
TWILIO_ACCOUNT_SID = 'US153b06ac498ef1b403ab552f6673f964'
TWILIO_AUTH_TOKEN = '8PJ3VNDJV6BWD5H7VD92LSCW'
TWILIO_PHONE_NUMBER = '+2330203419613'  #Twilio phone number
SENDGRID_API_KEY = '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'  #For email messaging


#Enable debug logging
logging.basicConfig(level=logging.DEBUG)

#WhatsApp Messaging
def send_whatsapp_message(to, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            to=f'whatsapp:{to}'
        )
        print(f"WhatsApp message sent to {to}: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
        return False

#Email Messaging
def send_email(to_email, subject, content):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email("tynochagaka@gmail.com")  #Replace with your sender email
    to_email = To(to_email)
    content = Content("text/plain", content)  #Use "text/html" for HTML emails
    
    #Disable SSL verification (not recommended for production)
    context = ssl._create_unverified_context()
    
    try:
        response = sg.client.mail.send.post(request_body=mail.get(), ssl_context=context)
        print(f"Email sent to {to_email}: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

#Routes
@app.route('/send_whatsapp', methods=['POST'])
def send_whatsapp():
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


#User model
class Users(UserMixin):
    def __init__(self, id, username, password, first_name=None, last_name=None, phone=None, role=None, address=None, email=None, points=0, badges="", bio =None, profile_picture=None):
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
        self.profile_picture=profile_picture

#User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return Users(**user_data)
    return None

def get_current_user():
    return current_user

#SocketIO Event Handlers
@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    emit('receive_message', {
        'message': data['message'],
        'username': data['username']
    }, room=room)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('receive_message', {
        'message': f'{username} has joined the room.',
        'username': 'System'
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('receive_message', {
        'message': f'{username} has left the room.',
        'username': 'System'
    }, room=room)

@app.route('/')
def home():
    #Example user data
    user_data = {
        'username': 'example_user',
        'role': 'Artist'  #or 'User' or 'Admin'
    }
    return render_template('index.html', user_data=user_data)


@app.route('/sketchboard')
@login_required
def sketchboard():
    try:
        #Fetch user data
        user_data = get_user_data(current_user.username)
        
        #Fetch leaderboard data
        leaderboard_data = get_leaderboard()
        
        #Fetch challenges data
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Challenges")
        challenges = cursor.fetchall()
        cursor.close()
        conn.close()
        
        #Render the sketchboard template with user_data, leaderboard_data, and challenges
        return render_template('sketchboard.html', user_data=user_data, leaderboard_data=leaderboard_data, challenges=challenges)
    except Exception as e:
        print(f"Error in sketchboard route: {e}")  #Debug statement
        flash('An error occurred while loading the sketchboard.', 'error')
        return redirect(url_for('index'))  #Redirect to a safe page


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
        #Check if the user already has a score entry
        cursor.execute("SELECT score FROM leaderboard WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            #Update existing score
            new_score = result[0] + points
            cursor.execute("UPDATE leaderboard SET score = %s WHERE username = %s", (new_score, username))
        else:
            #Insert new score entry
            cursor.execute("INSERT INTO leaderboard (username, score) VALUES (%s, %s)", (username, points))

        conn.commit()
        return jsonify({'success': True})
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
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
                    
                    #Role-based redirection
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
            print(f"Database error: {e}")
            error = "There was an error processing your request. Please try again."

    return render_template('login.html', error=error)


#Configure upload folder

UPLOAD_FOLDER = "static/uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#Allowed file extensions for document uploads
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

#Function to check valid file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


from flask import flash, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash
import re
import pymysql

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
        #Get form data
        username = request.form.get("username", "").strip()
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "").strip()
        address = request.form.get("address", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirmPassword", "").strip()

        #Validate required fields
        if not all([username, first_name, last_name, phone, role, address, email, password]):
            flash("❌ All fields are required!", "error")
            return redirect(url_for("registration"))

        #Validate password match
        if password != confirm_password:
            flash("❌ Passwords do not match!", "error")
            return redirect(url_for("registration"))

        #Validate location
        if len(address) < 3:
            flash("❌ Location must be at least 3 characters", "error")
            return redirect(url_for("registration"))
        
        if re.match(r'^[0-9\s]+$', address):
            flash("❌ Location cannot be just numbers", "error")
            return redirect(url_for("registration"))

        #Validate email format
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9._-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("❌ Invalid email format", "error")
            return redirect(url_for("registration"))

        #Check username availability again (race condition protection)
        conn = None
        try:
            conn = create_connection()
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash("❌ Username is already taken", "error")
                    return redirect(url_for("registration"))

                #Hash password only after all validations pass
                hashed_password = generate_password_hash(password)

                #Insert user
                cursor.execute("""
                    INSERT INTO Users (username, first_name, last_name, phone, role, address, email, password)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (username, first_name, last_name, phone, role, address, email, hashed_password))
                
                conn.commit()

                #Handle redirection based on role
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

        #✅ Define pre-set security questions
        security_question1 = "What is the name of your first school?"
        security_question2 = "What is your favorite artist or artwork?"

        try:
            #✅ Check if user exists in Users table
            cursor.execute("SELECT username FROM Users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                flash("❌ Error: User does not exist. Please register first.", "error")
                return redirect(url_for("registration"))

            #✅ Insert into ArtistVerification table
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


@app.route('/dashboard')
@login_required
def dashboard():
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
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('userdashboard.html', challenges=challenges, user=current_user)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

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

def get_leaderboard():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    #Fetch leaderboard data sorted by score in descending order
    cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
    leaderboard_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return leaderboard_data

@app.route('/get_statistics')
@login_required
def get_statistics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #Fetch total users
        cursor.execute("SELECT COUNT(*) AS total_users FROM Users")
        total_users = cursor.fetchone()['total_users']

        #Fetch total artwork submissions
        cursor.execute("SELECT COUNT(*) AS total_artwork FROM Artwork")
        total_artwork = cursor.fetchone()['total_artwork']

        #Fetch active projects (e.g., challenges with a deadline in the future)
        cursor.execute("SELECT COUNT(*) AS active_projects FROM Challenges WHERE deadline > %s", (datetime.utcnow(),))
        active_projects = cursor.fetchone()['active_projects']

        cursor.close()
        conn.close()

        #Return the statistics as JSON
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

        #Fetch recent submissions with dates
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

        #Format the dates for better readability
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

        #Fetch all users
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

        #Delete the user
        cursor.execute("DELETE FROM Users WHERE id = %s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error removing user: {e}")
        return jsonify({'error': 'Failed to remove user'}), 500
    

@app.route('/leaderboard')
@login_required
def leaderboard():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        print("Fetching leaderboard data...")  #Debug statement
        
        cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10")
        leaderboard_data = cursor.fetchall()
        
        print(f"Leaderboard data fetched: {leaderboard_data}")  #Debug statement
        
        cursor.close()
        connection.close()
        
        return render_template('leaderboard.html', leaderboard_data=leaderboard_data)
    except Exception as e:
        print(f"Error fetching leaderboard data: {e}")  #Debug statement
        flash('An error occurred while fetching the leaderboard.', 'error')
        return redirect(url_for('index'))  #Redirect to a safe page


@app.route('/submit_challenge/<int:challenge_id>', methods=['POST'])
@login_required
def submit_challenge(challenge_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Challenges WHERE id = %s", (challenge_id,))
    challenge = cursor.fetchone()

    if challenge:
        cursor.execute("UPDATE Users SET points = points + %s WHERE id = %s", (challenge['points_reward'], current_user.id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    return "Challenge not found!", 404

@app.route('/create_challenges', methods=['GET', 'POST'])
@login_required
def create_challenges():
    if request.method == 'POST':
        name = request.form.get("name")
        description = request.form.get("description")
        deadline = request.form.get("deadline")
        points_reward = request.form.get("points_reward", type=int)

        #Create a connection to the database
        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO challenges (name, description, deadline, points_reward)
                VALUES (%s, %s, %s, %s)
            """, (name, description, deadline, points_reward))
            conn.commit()
        except mysql.connector.Error as e:
            print(f"Database error: {e}")  #Log error for debugging
            conn.rollback()  #Rollback in case of error
            return "There was an error creating the challenge.", 500
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('dashboard'))  #Redirect to the dashboard after successful creation

    return render_template('create_challenges.html')  #Render the form for GET requests

@app.route('/art_challenges')
def art_challenges():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('art_challenges.html', user=user, username=username, user_data=user_data)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

#Route: Log user interactions
@app.route('/log_interaction', methods=['POST'])
def log_interaction():
    user_id = session.get('user_id', 'guest')  #Track session user
    data = request.json
    page_name = data.get("page")
    interaction_type = data.get("interaction")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_interactions (user_id, page_name, interaction_type) VALUES (%s, %s, %s)",
        (user_id, page_name, interaction_type),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Interaction logged successfully"})

#Route: Analyze interactions and return recommendations
@app.route('/get_recommendations')
def get_recommendations():
    user_id = session.get('user_id', 'guest')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT page_name, COUNT(*) as visits FROM user_interactions WHERE user_id = %s GROUP BY page_name ORDER BY visits DESC LIMIT 3",
        (user_id,)
    )
    top_pages = cursor.fetchall()
    conn.close()

    recommendations = [page[0] for page in top_pages]
    return jsonify({"recommended_pages": recommendations})


import hashlib
from PIL import Image
import imagehash

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_artwork():
    if request.method == 'POST':
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        tags = request.form.get("tags")
        media = request.files.get("media")

        #Validate required fields
        if not all([title, description, price, tags, media]):
            return jsonify({'success': False, 'message': 'Please fill in all fields and upload an artwork!'}), 400

        if media.filename == '':
            return jsonify({'success': False, 'message': 'No file selected!'}), 400

        #Generate file hash
        file_hash = hashlib.sha256(media.read()).hexdigest()
        media.seek(0)

        #Check for duplicates
        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM artwork WHERE file_hash = %s", (file_hash,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Artwork already exists!'}), 409  #Conflict

        #Save artwork
        filename = secure_filename(media.filename)
        file_path = os.path.join("static/uploads", filename)
        media.save(file_path)

        cursor.execute("""
            INSERT INTO artwork (title, description, price, tags, media, user_id, file_hash) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, description, price, tags, file_path, current_user.id, file_hash))
        conn.commit()

        return jsonify({'success': True, 'message': 'Artwork uploaded successfully!'}), 200

    return render_template("upload_artwork.html")

@app.route('/api/check_artwork', methods=['POST'])
@login_required
def check_artwork():
    if 'media' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    media = request.files['media']
    if media.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        #Generate file hash
        file_hash = hashlib.sha256(media.read()).hexdigest()
        media.seek(0)
        
        #Generate perceptual hash for images
        perceptual_hash = None
        if media.content_type.startswith('image'):
            try:
                img = Image.open(media.stream)
                perceptual_hash = str(imagehash.average_hash(img))
                media.seek(0)
            except Exception as e:
                app.logger.error(f"Image processing error: {str(e)}")
                return jsonify({'error': 'Error processing image'}), 400

        #Check database
        conn = create_connection()
        cursor = conn.cursor()
        
        try:
            #Check for exact duplicates
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

            #Check for similar images
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
            app.logger.error(f"Database error: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/view_artwork')
def view_artwork():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('view_artwork.html', user=user, username=username, user_data=user_data)

@app.route('/collaboration_hub')
def collaboration_hub():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('collaboration_hub.html', user=user, username=username, user_data=user_data)

@app.route('/marketplace')
def marketplace():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    #Create a database connection
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    #Fetch artworks from the Artwork table
    cursor.execute("SELECT * FROM artwork")
    artworks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    #Render the marketplace template with the artworks
    return render_template('marketplace.html', artworks=artworks, user=user, username=username, user_data=user_data)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        bio = request.form.get('bio')
        profile_picture = request.files.get('profile_picture')

        conn = create_connection()
        cursor = conn.cursor()

        #Update user information
        cursor.execute("""
            UPDATE Users 
            SET first_name = %s, last_name = %s, bio = %s 
            WHERE id = %s
        """, (first_name, last_name, bio, current_user.id))

        if profile_picture:
            #Save the profile picture
            profile_picture_filename = secure_filename(profile_picture.filename)
            profile_picture_path = os.path.join('static/profile_pics', profile_picture_filename)
            profile_picture.save(profile_picture_path)

            #Update the profile picture path in the database
            cursor.execute("""
                UPDATE Users 
                SET profile_picture = %s 
                WHERE id = %s
            """, (profile_picture_path, current_user.id))

        conn.commit()
        cursor.close()
        conn.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    user = load_user(current_user.id)
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    #Fetch artworks uploaded by the user
    cursor.execute("SELECT * FROM artwork WHERE user_id = %s", (user.id,))
    artworks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('profile.html', user=user, artworks=artworks, username=username, user_data=user_data)

@app.route('/workshops')
def workshops():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('workshops.html', user=user, username=username, user_data=user_data)

@app.route('/checkout')
def checkout():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('checkout.html', user=user, username=username, user_data=user_data)
PAYSTACK_SECRET_KEY = "sk_test_ed78162ac6ecfa0caadb9bc3346619e781498fb5"
@app.route('/pay', methods=['POST'])
def pay():
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
        "amount": int(amount) * 100,  #Convert to kobo
        "currency": currency
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Payment initialization failed"}), 500

@app.route('/pay/verify/<string:reference>')
def verify_payment(reference):
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
    }

    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data["data"]["status"] == "success":
            return "Payment successful"
        else:
            return "Payment failed", 400
    else:
        return "Verification failed", 500

@app.route('/virtual_gallery')
def virtual_gallery():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('virtual_gallery.html', user=user, username=username, user_data=user_data)

@app.route('/delete_artwork', methods=['DELETE'])
def delete_artwork():
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

@app.route('/create_challenge', methods=['POST'])
def create_challenge():
    name = request.form['name']
    description = request.form['description']
    deadline = request.form['deadline']
    points_reward = request.form['points_reward']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO challenges (name, description, deadline, points_reward) VALUES (%s, %s, %s, %s)",
                   (name, description, deadline, points_reward))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('challenges'))

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


@app.route('/task_management')
def artwork_management():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, user_id, title, description FROM artwork")
    artworks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('task_management.html', artworks=artworks)


@app.route('/settings')
def settings():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('settings.html', user=user, username=username, user_data=user_data)

@app.route('/display_challenges')
@login_required
def display_challenges():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    #Fetch all challenges
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('display.html', challenges=challenges, user=user, username=username, user_data=user_data)

@app.route('/user_management')
def user_management():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('user_management.html', user=user, username=username, user_data=user_data)

#Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="testDB"
    )

#Function to fetch messages from database
def fetch_messages(room):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, message, timestamp FROM messages WHERE room = %s ORDER BY timestamp ASC", (room,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages

#Function to log messages in the database
def log_message(username, room, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, room, message, timestamp) VALUES (%s, %s, %s, %s)",
                   (username, room, message, datetime.utcnow()))
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/message')
@login_required
def message():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    room = 'general'  #Set room name
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, message, timestamp FROM messages WHERE room = %s ORDER BY timestamp ASC", (room,))
    messages = cursor.fetchall()
    conn.close()
    
    return render_template('message.html', username=current_user.username, messages=messages, room=room, user_data=user_data)

def log_message(username, room, message):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, room, message, timestamp) VALUES (%s, %s, %s, %s)",
                   (username, room, message, datetime.utcnow()))
    conn.commit()
    cursor.close()
    conn.close()

@socketio.on('join')
def handle_join(data):
    username = current_user.username
    room = data['room']
    join_room(room)

    #Fetch previous messages for the room
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, message, timestamp FROM messages WHERE room = %s ORDER BY timestamp ASC", (room,))
    messages = cursor.fetchall()
    conn.close()

    #Send previous messages to the user
    for msg in messages:
        send({
            'username': msg['username'],
            'message': msg['message'],
            'timestamp': msg['timestamp'],
            'room': room
        }, room=room)

    system_message = f'{username} joined the chat!'
    log_message('System', room, system_message)
    send({'username': 'System', 'message': system_message}, room=room)

@socketio.on('send_message')
def handle_message(data):
    username = current_user.username
    room = data['room']
    message = data['message']

    #Log the message to the database
    log_message(username, room, message)

    #Send the message to the room
    send({'username': username, 'message': message, 'timestamp': datetime.utcnow(), 'room': room}, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    username = current_user.username
    system_message = f'{username} left the chat.'

    log_message('System', "General", system_message)
    send({'username': 'System', 'message': system_message}, broadcast=True)

def get_insights():
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT views, likes, shares FROM insights LIMIT 1")
    data = cursor.fetchone()
    connection.close()
    return data

@app.route('/insights')
def insights():
    data = get_insights()
    return render_template('insights.html', views=data["views"], likes=data["likes"], shares=data["shares"])

#Chat functionality
@app.route('/chat')
def chat():
    user = get_current_user()  #Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('chat.html', user=user, username=username, user_data=user_data)

#Define chatbot model globally
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
    max_length = data.get("max_length", 50)  #Default max length

    try:
        #Tokenize input
        inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True).to(device)

        #Generate response
        outputs = chatbot_model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_beams=5,
            early_stopping=True
        )

        #Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#PayPal Configuration
paypalrestsdk.configure({
    "mode": "sandbox",  #Change to "live" for production
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
})

@app.route('/process_payment', methods=['POST'])
def process_payment():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    payment_method = request.form['payment_method']
    total_amount = 100.00  #Example amount; replace with actual artwork price

    if payment_method == 'paypal':
        #Create a PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
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

        #Create the payment
        if payment.create():
            print("Payment created successfully")
            for link in payment.links:
                if link.rel == "approval_url":
                    #Redirect user to PayPal for approval
                    return redirect(link.href)
        else:
            print(payment.error)
            flash('Payment creation failed. Please try again.', 'danger')
            return redirect(url_for('checkout'))

    elif payment_method == 'momo':
        #Implement MoMo payment processing logic here
        flash('MoMo payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    elif payment_method == 'credit_card':
        #Implement credit card processing logic here
        flash('Credit card payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    else:
        flash('Invalid payment method selected.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/payment_success')
def payment_success():
    flash('Payment completed successfully! Thank you for your purchase.', 'success')
    return redirect(url_for('artworks'))  #Redirect to artworks page or confirmation page

@app.route('/payment_cancel')
def payment_cancel():
    flash('Payment was cancelled. Please try again.', 'warning')
    return redirect(url_for('checkout'))  #Redirect back to the checkout page

if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    load_model()  #Load your model if applicable
    socketio.run(app, debug=True)

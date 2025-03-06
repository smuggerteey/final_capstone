from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector
import pymysql
from werkzeug.utils import secure_filename
import torch
from flask_mail import Mail, Message # type: ignore
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from datetime import datetime
import os

# Ensure the profile pictures directory exists
if not os.path.exists('static/profile_pics'):
    os.makedirs('static/profile_pics')
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import paypalrestsdk  # Make sure to install this if using PayPal

app = Flask(__name__)
# Configure Flask-Mail
mail = Mail(app)


# Set your secret key
app.secret_key = 'tinotenda'  # Change this to a strong unique key

# MySQL Database Configuration
db_config = {
    'user': 'root',
    'password': '',  # Replace with your MySQL password
    'host': 'localhost',
    'database': 'testDB'  # Replace with your database name
}

# Create a connection to the MySQL database
def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        if conn.is_connected():
            print("Connected to MySQL database")
    except mysql.connector.Error as e:
        print(f"The error '{e}' occurred")
    return conn

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


# User model
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

# User loader function for Flask-Login
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

# SocketIO Event Handlers
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

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
                print(f"User found: {user_data}")  # Debugging line
                if check_password_hash(user_data['password'], password):
                    user = Users(**user_data)
                    login_user(user)
                    
                    # Role-based redirection
                    if username in ["smuggerteey", "cicada403"]:
                        return redirect(url_for('admindashboard'))
                    elif user_data['role'] == 'Artist':
                        return redirect(url_for('dashboard'))
                    elif user_data['role'] == 'Regular User':
                        return redirect(url_for('userdashboard'))
                    else:
                        return "Invalid role! Contact admin."
                else:
                    return "Invalid credentials!"  # Password mismatch
            else:
                return "User not found!"  # User not found in DB
        
        except mysql.connector.Error as e:
            print(f"Database error: {e}")  # Log any database connection errors
            return "There was an error with the database."

    return render_template('login.html')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions for document uploads
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Function to check valid file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form.get("username")
        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        phone = request.form.get("phone")
        role = request.form.get("role")
        address = request.form.get("address")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmPassword")

        if password != confirm_password:
            flash("❌ Passwords do not match!", "error")
            return redirect(url_for("registration"))

        hashed_password = generate_password_hash(password)

        conn = create_connection()
        cursor = conn.cursor()

        try:
            # ✅ Insert user into Users table
            cursor.execute("""
                INSERT INTO Users (username, first_name, last_name, phone, role, address, email, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, first_name, last_name, phone, role, address, email, hashed_password))
            
            conn.commit()
            cursor.close()
            conn.close()

            # ✅ If query param "redirect" exists, handle redirection
            if request.args.get("redirect") == "artist-verification" and role == "Artist":
                return redirect(url_for("artist_verification", username=username))

            return redirect(url_for("login"))

        except pymysql.MySQLError as e:
            flash(f"❌ Database Error: {str(e)}", "error")
            return redirect(url_for("registration"))

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
    
    # Fetch leaderboard data sorted by score in descending order
    cursor.execute("SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 3")
    leaderboard_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return leaderboard_data

@app.route('/leaderboard')
@login_required
def leaderboard():
    leaderboard_data = get_leaderboard()  # Fetch leaderboard data
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)


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

        # Create a connection to the database
        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO challenges (name, description, deadline, points_reward)
                VALUES (%s, %s, %s, %s)
            """, (name, description, deadline, points_reward))
            conn.commit()
        except mysql.connector.Error as e:
            print(f"Database error: {e}")  # Log error for debugging
            conn.rollback()  # Rollback in case of error
            return "There was an error creating the challenge.", 500
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('dashboard'))  # Redirect to the dashboard after successful creation

    return render_template('create_challenges.html')  # Render the form for GET requests

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/art_challenges')
def art_challenges():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('art_challenges.html', user=user, username=username, user_data=user_data)

@app.route('/upload_artwork', methods=['GET', 'POST'])
@login_required
def upload_artwork():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        tags = request.form['tags']
        media = request.files['media']

        if media:
            media_filename = secure_filename(media.filename)
            media_path = os.path.join('uploads', media_filename)
            media.save(media_path)

            # Save artwork information to the database
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO artwork (title, description, price, tags, media, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, description, price, tags, media_path, current_user.id))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('art_challenges'))  # Redirect after successful upload

    return render_template('upload_artwork.html')

@app.route('/view_artwork')
def view_artwork():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('view_artwork.html', user=user, username=username, user_data=user_data)

@app.route('/collaboration_hub')
def collaboration_hub():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('collaboration_hub.html', user=user, username=username, user_data=user_data)

@app.route('/marketplace')
def marketplace():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    # Create a database connection
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch artworks from the Artwork table
    cursor.execute("SELECT * FROM artwork")
    artworks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Render the marketplace template with the artworks
    return render_template('marketplace.html', artworks=artworks, user=user, username=username, user_data=user_data)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        bio = request.form.get('bio')
        profile_picture = request.files.get('profile_picture')

        conn = create_connection()
        cursor = conn.cursor()

        # Update user information
        cursor.execute("""
            UPDATE Users 
            SET first_name = %s, last_name = %s, bio = %s 
            WHERE id = %s
        """, (first_name, last_name, bio, current_user.id))

        if profile_picture:
            # Save the profile picture
            profile_picture_filename = secure_filename(profile_picture.filename)
            profile_picture_path = os.path.join('static/profile_pics', profile_picture_filename)
            profile_picture.save(profile_picture_path)

            # Update the profile picture path in the database
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

    # Fetch artworks uploaded by the user
    cursor.execute("SELECT * FROM artwork WHERE user_id = %s", (user.id,))
    artworks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('profile.html', user=user, artworks=artworks, username=username, user_data=user_data)

@app.route('/workshops')
def workshops():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('workshops.html', user=user, username=username, user_data=user_data)

@app.route('/checkout')
def checkout():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('checkout.html', user=user, username=username, user_data=user_data)


@app.route('/virtual_gallery')
def virtual_gallery():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('virtual_gallery.html', user=user, username=username, user_data=user_data)

@app.route('/task_management')
def task_management():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('task_management.html', user=user, username=username, user_data=user_data)

@app.route('/settings')
def settings():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('settings.html', user=user, username=username, user_data=user_data)

@app.route('/display_challenges')
@login_required
def display_challenges():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all challenges
    cursor.execute("SELECT * FROM Challenges")
    challenges = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('display.html', challenges=challenges, user=user, username=username, user_data=user_data)

@app.route('/user_management')
def user_management():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('user_management.html', user=user, username=username, user_data=user_data)

# Function to connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="testDB"
    )

# Function to fetch messages from database
def fetch_messages(room):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, message, timestamp FROM messages WHERE room = %s ORDER BY timestamp ASC", (room,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages

# Function to log messages in the database
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
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    room = 'general'  # Set room name
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

    # Fetch previous messages for the room
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, message, timestamp FROM messages WHERE room = %s ORDER BY timestamp ASC", (room,))
    messages = cursor.fetchall()
    conn.close()

    # Send previous messages to the user
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

    # Log the message to the database
    log_message(username, room, message)

    # Send the message to the room
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

# Chat functionality
@app.route('/chat')
def chat():
    user = get_current_user()  # Function to get the logged-in user
    username = user.username
    user_data = {'role': user.role} 
    return render_template('chat.html', user=user, username=username, user_data=user_data)

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


# PayPal Configuration
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
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
    total_amount = 100.00  # Example amount; replace with actual artwork price

    if payment_method == 'paypal':
        # Create a PayPal payment
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
                    "currency": "USD"
                },
                "description": "Purchase of artwork"
            }]
        })

        # Create the payment
        if payment.create():
            print("Payment created successfully")
            for link in payment.links:
                if link.rel == "approval_url":
                    # Redirect user to PayPal for approval
                    return redirect(link.href)
        else:
            print(payment.error)
            flash('Payment creation failed. Please try again.', 'danger')
            return redirect(url_for('checkout'))

    elif payment_method == 'momo':
        # Implement MoMo payment processing logic here
        flash('MoMo payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    elif payment_method == 'credit_card':
        # Implement credit card processing logic here
        flash('Credit card payment processing is not implemented yet.', 'warning')
        return redirect(url_for('checkout'))

    else:
        flash('Invalid payment method selected.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/payment_success')
def payment_success():
    flash('Payment completed successfully! Thank you for your purchase.', 'success')
    return redirect(url_for('artworks'))  # Redirect to artworks page or confirmation page

@app.route('/payment_cancel')
def payment_cancel():
    flash('Payment was cancelled. Please try again.', 'warning')
    return redirect(url_for('checkout'))  # Redirect back to the checkout page

if __name__ == "__main__":
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    load_model()  # Load your model if applicable
    socketio.run(app, debug=True)
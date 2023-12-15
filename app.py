from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import rsa
import random
import string
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

user_credentials = {
    'user1@example.com': {'password': 'password1', 'username': 'user1'},
    'user2@example.com': {'password': 'password2', 'username': 'user2'},
    'user3@example.com': {'password': 'password3', 'username': 'user3'},
}

chat_rooms = {}

def generate_chat_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def caesar_cipher(message):
    current_time = datetime.datetime.now().hour
    shift = current_time + 10 
    encrypted_message = ""

    for char in message:
        if char.isalpha():
            if char.isupper():
                encrypted_message += chr(((ord(char) - 65 + shift) % 26) + 65)
            else:
                encrypted_message += chr(((ord(char) - 97 + shift) % 26) + 97)
        elif char.isnumeric():
            encrypted_message += chr(((ord(char) - 48 + shift) % 10) + 48)
        else:
            encrypted_message += char  

    return encrypted_message

def get_username_by_email(email):
    if email in user_credentials:
        return user_credentials[email]['username']
    else:
        return None

@app.route('/')
def home():
    if 'logged_in' not in session:
        session['logged_in'] = False

    chat_rooms_data = None

    if session['logged_in']:
        chat_rooms_data = chat_rooms

    return render_template('home.html', chat_rooms=chat_rooms_data)


@app.route('/create', methods=['POST'])
def create_chat():
    chat_code = generate_chat_code()
    creator_email = session.get('email') 
    chat_rooms[chat_code] = {
        'creator_email': creator_email,
        'messages': [],
        'public_key': rsa.newkeys(512)[0]  
    }
    return redirect(url_for('chat', chat_code=chat_code))

@app.route('/enter', methods=['POST'])
def enter_chat():
    chat_code = request.form['chat_code']
    if chat_code in chat_rooms:
        return redirect(url_for('chat', chat_code=chat_code))
    else:
        return "Chat room not found."

@app.route('/chat/<chat_code>')
def chat(chat_code):
    if chat_code not in chat_rooms:
        return "Chat room not found."

    return render_template('chat.html', chat_code=chat_code, messages=chat_rooms[chat_code]['messages'])

@socketio.on('send_message')
def handle_message(data):
    chat_code = data['chat_code']
    message = data['message']
    sender_username = session.get('username')  
    encrypted_message_caesar = caesar_cipher(message)
    encrypted_message_rsa = rsa.encrypt(encrypted_message_caesar.encode(), chat_rooms[chat_code]['public_key'])

    chat_rooms[chat_code]['messages'].append({
        'sender': sender_username,  
        'message': message,
        'encrypted_message_caesar': encrypted_message_caesar,
        'encrypted_message_rsa': encrypted_message_rsa,
    })

    emit('update_messages', chat_rooms[chat_code]['messages'], broadcast=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in user_credentials and user_credentials[email]['password'] == password:
            session['logged_in'] = True
            session['email'] = email  
            session['username'] = user_credentials[email]['username']  
            return redirect(url_for('home'))
        else:
            return "Invalid email or password."

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)  
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, debug=False, allow_unsafe_werkzeug=True)

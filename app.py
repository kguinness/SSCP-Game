# Step 1: Setting Up the Database (SQLite)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, flash, url_for
import os

# Initialize the database connection and create tables
def initialize_database():
    with sqlite3.connect('game_database.db') as conn:
        cursor = conn.cursor()

        # Create a Users table to store user login information
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            high_score INTEGER DEFAULT 0
        )
        ''')

        # Create a Questions table for storing quiz questions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
        ''')

# Initialize the database
initialize_database()

# Step 2: Flask Application for Login/Register
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        
        try:
            with sqlite3.connect('game_database.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, password_hash))
                conn.commit()
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            return redirect(url_for('register'))
        
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('login'))

        with sqlite3.connect('game_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, password_hash, high_score FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user is None:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        if check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['high_score'] = user[3]
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))
    return render_template('login.html')

# Home route
@app.route('/home', methods=['GET'])
def home():
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

# Game route
@app.route('/game', methods=['GET'])
def game():
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))
    return render_template('game.html', username=session['username'], high_score=session['high_score'])

# Add a route to update the high score
@app.route('/update_high_score', methods=['POST'])
def update_high_score():
    if 'user_id' in session:
        high_score = request.json.get('high_score', 0)
        with sqlite3.connect('game_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET high_score = ? WHERE user_id = ?", (high_score, session['user_id']))
            conn.commit()
    return ('', 204)

# Logout route
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

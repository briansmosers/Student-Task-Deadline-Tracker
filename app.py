#this is the backend

import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

users = [
    {"id": 1, "username": "User0001", "pfp_url": "profile_photo.png"}
]

user_profile = {
    "Username" : "ladiesman217",
    "pfp_url" : "profile_photo.png"
}

# Mock database
assignments = [
    {"task": "Math Problem Set", "due": "2026-04-25", "difficulty": "Hard"},
    {"task": "History Essay", "due": "2026-04-30", "difficulty": "Medium"},
    {"task": "Read Chapter 1", "due": "2026-04-22", "difficulty": "Easy"},
]

def create_new_user():
    global user_counter
    user_counter += 1
    # formats number to 4 digits, e.g., 2 becomes "0002"
    new_name = f"User{user_counter:04d}" 
    new_user = {"id": user_counter, "username": new_name, "pfp_url": "profile_photo.png"}
    users.append(new_user)
    return new_user

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    current_user = users[0] # Using your list logic
    
    if request.method == 'POST':
        # 1. Handle Username
        new_username = request.form.get('username')
        if new_username:
            current_user['username'] = new_username

        # 2. Handle File Upload
        if 'pfp_file' in request.files:
            file = request.files['pfp_file']
            if file.filename != '':
                # Save the file to the uploads folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                
                # Update the user data to point to the new local path
                current_user['pfp_url'] = url_for('static', filename='uploads/' + file.filename)
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=current_user)

@app.route('/')
def index():
    return render_template('index.html', assignments=assignments)

@app.route('/add', methods=['POST'])
def add_assignment():
    task = request.form.get('task')
    due = request.form.get('due')
    difficulty = request.form.get('difficulty')
    
    if task and due:
        assignments.append({"task": task, "due": due, "difficulty": difficulty})
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
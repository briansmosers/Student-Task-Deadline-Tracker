from flask import Flask, render_template, request, redirect, session, url_for
import pyrebase

app = Flask(__name__)
app.secret_key = "your_secret_key" 

config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "your-project.firebaseapp.com",
    "databaseURL": "https://your-project.firebaseio.com",
    "storageBucket": "your-project.appspot.com"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        # 1. Grab all the new data from the form
        name = request.form.get('name')
        age = request.form.get('age')
        university = request.form.get('university')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # 2. Create the user in Firebase Auth
            user = auth.create_user_with_email_and_password(email, password)
            
            # 3. Save the extra "Student Profile" data to the Database
            # We use user['localId'] as the unique ID for this student
            student_profile = {
                "name": name,
                "age": age,
                "university": university,
                "email": email
            }
            
            # This saves the data under a 'users' folder in your Firebase
            db.child("users").child(user['localId']).set(student_profile)
            
            return redirect(url_for('index')) 
        except Exception as e:
            return f"Registration Failed: {str(e)}"
            
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        session['user'] = user['localId']
        return "Logged in! Move to Dashboard."
    except:
        return "Login Failed. Check credentials."

if __name__ == '__main__':
    app.run(debug=True)
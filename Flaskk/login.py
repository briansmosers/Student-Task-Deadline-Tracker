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

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            auth.create_user_with_email_and_password(email, password)
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error: {str(e)}"
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
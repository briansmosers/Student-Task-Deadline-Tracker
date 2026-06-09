from flask import Flask, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Required for session tracking later

@app.route('/')
def index():
    return render_template('landing.html')

if __name__ == '__main__':
    app.run(debug=True)
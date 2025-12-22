from flask import Flask, render_template

# THIS LINE IS CRITICAL: The variable must be named 'app'
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
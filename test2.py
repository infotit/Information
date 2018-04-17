from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    print("Modified...")
    return 'test.py...'


if __name__ == '__main__':
    app.run(debug=True)



from flask import Flask

app = Flask(__name__)


@app.route('/')
def homepage():
    return 'hello world'


app.run(host='0.0.0.0')

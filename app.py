import os
from flask import Flask
from models import db, User, Movie
from data_manager import DataManager

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'movies.db')
app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

data_manager = DataManager()

@app.route('/')
def home():
    return "Welcome to MoviWeb App!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    #app.run(debug=True, host='0.0.0.0', port=5002)

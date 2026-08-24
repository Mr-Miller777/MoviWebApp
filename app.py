import os

from flask import Flask, render_template, request, url_for, flash, redirect
from dotenv import load_dotenv
import requests

from models import db, User, Movie
from data_manager import DataManager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
OMDB_API_KEY = os.environ.get('OMDB_API_KEY')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'movies.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

data_manager = DataManager()


@app.route('/')
def home():
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def add_user():
    name = request.form.get('name')
    if name:
        data_manager.create_user(name)
        flash(f'User "{name}" added successfully.', 'success')
    else:
        flash('User name cannot be empty.', 'error')
    return redirect(url_for('home'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def list_movies(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home'))

    movies = data_manager.get_movies(user_id)
    return render_template('movies.html', user=user, movies=movies)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not fond.', 'error')
        return redirect(url_for('home'))

    title = request.form.get('title')
    if not title:
        flash('Movie title cannot be empty.', 'error')
        return redirect(url_for('list_movies', user_id=user_id))

    if not OMDB_API_KEY:
        flash('OMDb API key is not configured.', 'error')
        return redirect(url_for('list_movies', user_id=user_id))

    url = f'http://www.omdbapi.com/'
    params = {'apikey': OMDB_API_KEY, 't': title}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        flash(f'Could not reach OMDb API: {e}', 'error')
        return redirect(url_for('list_movies', user_id=user_id))

    if data.get('Response') == 'True':
        director = data.get('Director', '')
        year_str = data.get('Year', '')
        year = int(year_str) if year_str.isdigit() else None
        poster_url =data.get('Poster', '')

        new_movie = Movie(
            name=title,
            director=director,
            year=year,
            poster_url=poster_url,
            user_id=user_id
        )
        data_manager.add_movie(new_movie)
        flash(f'Movie "{title}" added.', 'success')
    else:
        flash(f'Movie "{title}" not found on OMDb.', 'error')

    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    new_title =request.form.get('title')
    if not new_title:
        flash('New title cannot be empty.', 'error')
    else:
        movi = data_manager.update_movie(movie_id, new_title)
        if movi:
            flash(f'Movie title updated to "{new_title}".', 'success')
        else:
            flash(f'Movie not found.', 'error')
    return redirect(url_for('list_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    if data_manager.delete_movie(movie_id):
        flash('Movie deleted.', 'success')
    else:
        flash('Movie not found.', 'error')
    return redirect(url_for('list_movies', user_id=user_id))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    #app.run(debug=True, host='0.0.0.0', port=5002)

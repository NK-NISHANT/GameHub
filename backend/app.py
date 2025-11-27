import os
import sys
import subprocess
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, set_access_cookies, verify_jwt_in_request, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['MONGODB_URI'] = os.getenv('MONGODB_URI')
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

CORS(app)
jwt = JWTManager(app)

try:
    mongo = MongoClient(app.config['MONGODB_URI'])
    db = mongo.get_default_database()
    print("✅ Connected to MongoDB!")
except Exception as e:
    print(f"❌ Database Error: {e}")

def get_current_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        if uid:
            return db.users.find_one({'_id': ObjectId(uid)})
    except:
        return None
    return None

def get_leaderboard_data():
    scores = list(db.scores.find({}).sort('score', -1).limit(15))
    for s in scores:
        u = db.users.find_one({'_id': s['user_id']})
        s['username'] = u['username'] if u else "Unknown"
        if 'game_id' not in s:
            s['game_id'] = 'snake'
    return scores

def launch_game_process(script_name):
    user_id = get_jwt_identity()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    token = create_access_token(identity=str(user_id))
    game_path = os.path.join("games", script_name)
    subprocess.Popen([sys.executable, game_path, token, user['username']])

@app.route('/')
def index():
    return render_template('index.html', scores=get_leaderboard_data(), user=get_current_user())

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/logout')
def logout():
    resp = redirect(url_for('login_page'))
    unset_jwt_cookies(resp)
    return resp

@app.route('/launch/<game_name>')
@jwt_required()
def launch_game(game_name):
    valid_games = ['snake', 'sudoku', 'memory', 'gem']
    if game_name in valid_games:
        launch_game_process(f"{game_name}.py")
    return redirect(url_for('index'))

@app.route('/api/register', methods=['POST'])
def register():
    u = request.form.get('username')
    p = request.form.get('password')
    if db.users.find_one({'username': u}):
        return "User exists!"
    db.users.insert_one({'username': u, 'password': generate_password_hash(p)})
    return redirect(url_for('login_page'))

@app.route('/api/login', methods=['POST'])
def login():
    u = request.form.get('username')
    p = request.form.get('password')
    user = db.users.find_one({'username': u})
    if not user or not check_password_hash(user['password'], p):
        return "Invalid credentials"
    token = create_access_token(identity=str(user['_id']))
    resp = redirect(url_for('index'))
    set_access_cookies(resp, token)
    return resp

@app.route('/api/score', methods=['POST'])
@jwt_required()
def save_score():
    data = request.get_json()
    db.scores.insert_one({
        'user_id': ObjectId(get_jwt_identity()),
        'game_id': data.get('game_id', 'snake'),
        'score': data['score'],
        'date': datetime.now()
    })
    return jsonify({'msg': 'Saved'}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)
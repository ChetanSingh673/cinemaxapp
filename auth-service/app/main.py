from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os, re

app = Flask(__name__)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/authdb')
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.authdb

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip().lower()
    if not username or not email:
        return jsonify({'error': 'Username and email required'}), 400
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    user_doc = {
        'username': username, 'email': email,
        'last_login': datetime.utcnow().isoformat()
    }
    db.users.update_one({'email': email}, {'$set': user_doc}, upsert=True)
    return jsonify({'status': 'success', 'user': {'username': username, 'email': email}})

@app.route('/auth/user/<email>')
def get_user(email):
    user = db.users.find_one({'email': email.lower()}, {'_id': 0})
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'auth-service'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

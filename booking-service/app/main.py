from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os, random

app = Flask(__name__)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/bookingdb')
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.bookingdb

MOVIE_SERVICE = os.environ.get('MOVIE_SERVICE_URL', 'http://movie-service:5002')

SEAT_CATEGORIES = [
    {"name": "Recliner", "price": 500, "rows": ["A", "B"]},
    {"name": "Premium", "price": 320, "rows": ["C", "D", "E", "F"]},
    {"name": "Executive", "price": 220, "rows": ["G", "H", "I", "J"]},
    {"name": "Classic", "price": 150, "rows": ["K", "L", "M", "N"]},
]
SEATS_PER_ROW = 14

def get_or_create_seats(movie_id, theatre_id, show_time):
    key = f"{movie_id}_{theatre_id}_{show_time}"
    existing = db.seat_layouts.find_one({"key": key})
    if existing:
        return existing
    categories = []
    for cat in SEAT_CATEGORIES:
        rows = []
        for row_label in cat["rows"]:
            seats = []
            for i in range(1, SEATS_PER_ROW + 1):
                booked = random.random() < 0.30
                seats.append({"id": f"{row_label}{i}", "available": not booked})
                if i == 7:
                    seats.append("gap")
            rows.append({"label": row_label, "seats": seats})
        categories.append({"name": cat["name"], "price": cat["price"], "rows": rows})
    layout = {
        "key": key,
        "movie_id": movie_id,
        "theatre_id": theatre_id,
        "show_time": show_time,
        "categories": categories,
        "created_at": datetime.utcnow().isoformat()
    }
    db.seat_layouts.insert_one(layout)
    layout["_id"] = str(layout["_id"])
    return layout

@app.route('/seats/<movie_id>/<theatre_id>/<show_time>')
def get_seats(movie_id, theatre_id, show_time):
    import requests as req
    try:
        movie_resp = req.get(f"{MOVIE_SERVICE}/movie/{movie_id}", timeout=5)
        movie_data = movie_resp.json() if movie_resp.status_code == 200 else {}
        movie_title = movie_data.get('title', movie_id)
        theatre_name = show_time
        for theatre in movie_data.get('theatres', []):
            if theatre['id'] == theatre_id:
                theatre_name = theatre['name']
                break
    except:
        movie_title = movie_id
        theatre_name = theatre_id

    layout = get_or_create_seats(movie_id, theatre_id, show_time)
    if "_id" in layout:
        layout["_id"] = str(layout["_id"])
    layout["movie_title"] = movie_title
    layout["theatre_name"] = theatre_name
    return jsonify(layout)

@app.route('/booking', methods=['POST'])
def create_booking():
    data = request.get_json()
    booking = {
        "movie_id": data.get("movie_id"),
        "theatre_id": data.get("theatre_id"),
        "show_time": data.get("show_time"),
        "seats": data.get("seats", []),
        "user": data.get("user"),
        "status": "confirmed",
        "booked_at": datetime.utcnow().isoformat()
    }
    result = db.bookings.insert_one(booking)
    booking["_id"] = str(result.inserted_id)
    return jsonify(booking)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'booking-service'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)

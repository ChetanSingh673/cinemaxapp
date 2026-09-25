from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os, random, string, requests as req

app = Flask(__name__)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/paymentdb')
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.paymentdb

MOVIE_SERVICE   = os.environ.get('MOVIE_SERVICE_URL',   'http://movie-service:5002')
BOOKING_SERVICE = os.environ.get('BOOKING_SERVICE_URL', 'http://booking-service:5003')

def gen_booking_id():
    return 'CB' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/payment/process', methods=['POST'])
def process_payment():
    data = request.get_json()
    card_number = data.get('card_number', '').replace(' ', '')
    cvv         = data.get('cvv', '')
    booking_info = data.get('booking_info', {})

    if len(card_number) < 13 or not cvv:
        return jsonify({'error': 'Invalid payment details'}), 400

    # Fetch movie & theatre details
    movie_title  = booking_info.get('movie_id', 'Unknown Movie')
    theatre_name = booking_info.get('theatre_id', 'Unknown Theatre')
    try:
        m_resp = req.get(f"{MOVIE_SERVICE}/movie/{booking_info.get('movie_id','')}", timeout=5)
        if m_resp.status_code == 200:
            m = m_resp.json()
            movie_title = m.get('title', movie_title)
            for t in m.get('theatres', []):
                if t['id'] == booking_info.get('theatre_id'):
                    theatre_name = t['name']
    except:
        pass

    seats     = booking_info.get('seats', [])
    seat_count = len(seats)
    base_price = 280
    amount = seat_count * base_price

    booking_id = gen_booking_id()
    payment_doc = {
        "booking_id":   booking_id,
        "movie_id":     booking_info.get('movie_id'),
        "movie_title":  movie_title,
        "theatre_id":   booking_info.get('theatre_id'),
        "theatre_name": theatre_name,
        "show_time":    booking_info.get('show_time'),
        "seats":        seats,
        "user":         booking_info.get('user', {}),
        "amount":       amount,
        "card_last4":   card_number[-4:],
        "status":       "success",
        "booking_date": datetime.utcnow().strftime("%d %b %Y"),
        "paid_at":      datetime.utcnow().isoformat()
    }
    db.payments.insert_one(payment_doc)

    # Notify booking service
    try:
        req.post(f"{BOOKING_SERVICE}/booking", json={
            "movie_id":   booking_info.get('movie_id'),
            "theatre_id": booking_info.get('theatre_id'),
            "show_time":  booking_info.get('show_time'),
            "seats":      seats,
            "user":       booking_info.get('user')
        }, timeout=5)
    except:
        pass

    payment_doc.pop('_id', None)
    return jsonify(payment_doc)

@app.route('/payment/history/<email>')
def payment_history(email):
    payments = list(db.payments.find({'user.email': email}, {'_id': 0}))
    return jsonify(payments)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'payment-service'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=False)

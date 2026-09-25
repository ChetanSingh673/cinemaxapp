from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'bookmyshow-secret-2024')

AUTH_SERVICE    = os.environ.get('AUTH_SERVICE_URL',    'http://auth-service:5001')
MOVIE_SERVICE   = os.environ.get('MOVIE_SERVICE_URL',   'http://movie-service:5002')
BOOKING_SERVICE = os.environ.get('BOOKING_SERVICE_URL', 'http://booking-service:5003')
PAYMENT_SERVICE = os.environ.get('PAYMENT_SERVICE_URL', 'http://payment-service:5004')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = {'username': request.form.get('username'), 'email': request.form.get('email')}
    try:
        resp = requests.post(f'{AUTH_SERVICE}/auth/login', json=data, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            session['user'] = result['user']
            return redirect(url_for('cities'))
        return render_template('index.html', error='Login failed. Please try again.')
    except Exception as e:
        return render_template('index.html', error=f'Auth service unavailable: {str(e)}')

@app.route('/cities')
def cities():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('cities.html', user=session['user'])

@app.route('/movies/<city>')
def movies(city):
    if 'user' not in session:
        return redirect(url_for('index'))
    try:
        resp = requests.get(f'{MOVIE_SERVICE}/movies/{city}', timeout=5)
        movies_data = resp.json() if resp.status_code == 200 else []
    except:
        movies_data = []
    return render_template('movies.html', city=city, movies=movies_data, user=session['user'])

@app.route('/movie/<city>/<movie_id>')
def movie_detail(city, movie_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    try:
        resp = requests.get(f'{MOVIE_SERVICE}/movie/{movie_id}', timeout=5)
        movie = resp.json() if resp.status_code == 200 else {}
    except:
        movie = {}
    return render_template('movie_detail.html', city=city, movie=movie, user=session['user'])

@app.route('/seats/<movie_id>/<theatre_id>/<show_time>')
def seats(movie_id, theatre_id, show_time):
    if 'user' not in session:
        return redirect(url_for('index'))
    try:
        resp = requests.get(f'{BOOKING_SERVICE}/seats/{movie_id}/{theatre_id}/{show_time}', timeout=5)
        seat_data = resp.json() if resp.status_code == 200 else {}
    except:
        seat_data = {}
    return render_template('seats.html', movie_id=movie_id, theatre_id=theatre_id,
                           show_time=show_time, seat_data=seat_data, user=session['user'])

@app.route('/payment', methods=['POST'])
def payment():
    if 'user' not in session:
        return redirect(url_for('index'))
    booking_info = {
        'movie_id':   request.form.get('movie_id'),
        'theatre_id': request.form.get('theatre_id'),
        'show_time':  request.form.get('show_time'),
        'seats':      request.form.getlist('seats'),
        'user':       session['user']
    }
    session['booking_info'] = booking_info
    return render_template('payment.html', booking_info=booking_info, user=session['user'])

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user' not in session:
        return redirect(url_for('index'))
    payment_data = {
        'card_number': request.form.get('card_number'),
        'cvv':         request.form.get('cvv'),
        'expiry':      request.form.get('expiry'),
        'booking_info': session.get('booking_info', {})
    }
    try:
        resp = requests.post(f'{PAYMENT_SERVICE}/payment/process', json=payment_data, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            session.pop('booking_info', None)
            return render_template('confirmation.html', booking=result, user=session['user'])
        return render_template('payment.html',
                               booking_info=session.get('booking_info', {}),
                               error='Payment failed. Please try again.',
                               user=session['user'])
    except Exception as e:
        return render_template('payment.html',
                               booking_info=session.get('booking_info', {}),
                               error=f'Payment service error: {str(e)}',
                               user=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'frontend'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

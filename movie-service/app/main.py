from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os, json

app = Flask(__name__)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/moviedb')
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.moviedb

# ─── SEED DATA ───────────────────────────────────────────────────────────────
MOVIES_DATA = {
    "Chennai": [
        {
            "title": "Dune: Part Two", "rating": "8.7", "duration": 166,
            "language": "English", "certification": "UA", "genres": ["Sci-Fi","Adventure","Drama"],
            "poster_emoji": "🏜️", "poster_gradient": "linear-gradient(135deg,#8B4513,#D4A017,#8B4513)",
            "description": "Paul Atreides unites with Chani and the Fremen while seeking revenge against those who destroyed his family, facing a choice between his love and the fate of the universe.",
            "director": "Denis Villeneuve", "cast": ["Timothée Chalamet","Zendaya","Rebecca Ferguson"],
            "release_date": "1 Mar 2024",
            "theatres": [
                {"id":"th_che_1","name":"PVR IMAX Phoenix MarketCity","location":"Velachery, Chennai",
                 "features":["IMAX","Dolby Atmos","4K"],
                 "shows":[{"time":"10:00 AM","price":480,"availability":"Available"},{"time":"1:30 PM","price":480,"availability":"Fast Filling"},{"time":"7:00 PM","price":550,"availability":"Fast Filling"},{"time":"10:30 PM","price":480,"availability":"Available"}]},
                {"id":"th_che_2","name":"Rohini Silver Screens","location":"Koyambedu, Chennai",
                 "features":["Dolby Atmos","3D"],
                 "shows":[{"time":"9:30 AM","price":220,"availability":"Available"},{"time":"2:00 PM","price":220,"availability":"Available"},{"time":"6:30 PM","price":250,"availability":"Fast Filling"},{"time":"10:00 PM","price":220,"availability":"Available"}]},
                {"id":"th_che_3","name":"SPI Palazzo","location":"Anna Salai, Chennai",
                 "features":["Premium","Recliners"],
                 "shows":[{"time":"11:00 AM","price":350,"availability":"Available"},{"time":"3:00 PM","price":350,"availability":"Available"},{"time":"8:00 PM","price":400,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Oppenheimer", "rating": "8.9", "duration": 180,
            "language": "English", "certification": "UA", "genres": ["Drama","Thriller","History"],
            "poster_emoji": "☢️", "poster_gradient": "linear-gradient(135deg,#1a1a1a,#FF6B00,#1a1a1a)",
            "description": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.",
            "director": "Christopher Nolan", "cast": ["Cillian Murphy","Emily Blunt","Robert Downey Jr."],
            "release_date": "21 Jul 2023",
            "theatres": [
                {"id":"th_che_1","name":"PVR IMAX Phoenix MarketCity","location":"Velachery, Chennai",
                 "features":["IMAX","Dolby Atmos"],
                 "shows":[{"time":"9:00 AM","price":480,"availability":"Available"},{"time":"1:00 PM","price":480,"availability":"Available"},{"time":"5:30 PM","price":550,"availability":"Fast Filling"},{"time":"10:00 PM","price":480,"availability":"Available"}]},
                {"id":"th_che_4","name":"Escape Cinemas","location":"Anna Nagar, Chennai",
                 "features":["2D","3D"],
                 "shows":[{"time":"10:30 AM","price":200,"availability":"Available"},{"time":"3:30 PM","price":200,"availability":"Available"},{"time":"7:30 PM","price":220,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Avengers: Secret Wars", "rating": "8.5", "duration": 190,
            "language": "English/Tamil", "certification": "U", "genres": ["Action","Adventure","Sci-Fi"],
            "poster_emoji": "⚡", "poster_gradient": "linear-gradient(135deg,#1D3557,#E63946,#1D3557)",
            "description": "The Avengers face their greatest challenge yet as the multiverse collapses and heroes from different universes must unite to save all of existence.",
            "director": "Russo Brothers", "cast": ["Robert Downey Jr.","Chris Evans","Scarlett Johansson"],
            "release_date": "2 May 2025",
            "theatres": [
                {"id":"th_che_1","name":"PVR IMAX Phoenix MarketCity","location":"Velachery, Chennai",
                 "features":["IMAX","4DX","Dolby"],
                 "shows":[{"time":"9:00 AM","price":550,"availability":"Fast Filling"},{"time":"12:30 PM","price":550,"availability":"Fast Filling"},{"time":"4:00 PM","price":600,"availability":"Fast Filling"},{"time":"8:30 PM","price":600,"availability":"Available"}]},
                {"id":"th_che_2","name":"Rohini Silver Screens","location":"Koyambedu, Chennai",
                 "features":["3D","Dolby"],
                 "shows":[{"time":"10:00 AM","price":280,"availability":"Available"},{"time":"2:30 PM","price":280,"availability":"Fast Filling"},{"time":"7:00 PM","price":300,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Kalki 2898 AD", "rating": "7.8", "duration": 181,
            "language": "Telugu/Tamil", "certification": "UA", "genres": ["Action","Sci-Fi","Mythology"],
            "poster_emoji": "🌌", "poster_gradient": "linear-gradient(135deg,#0D0D2B,#4B0082,#0D0D2B)",
            "description": "Set in a dystopian future, the film follows a Supreme Yaskin who fears the birth of Kalki, the final avatar of Vishnu, meant to end his reign.",
            "director": "Nag Ashwin", "cast": ["Prabhas","Deepika Padukone","Amitabh Bachchan"],
            "release_date": "27 Jun 2024",
            "theatres": [
                {"id":"th_che_5","name":"Mayajaal Multiplex","location":"ECR, Chennai",
                 "features":["IMAX","3D"],
                 "shows":[{"time":"11:00 AM","price":320,"availability":"Available"},{"time":"3:00 PM","price":320,"availability":"Available"},{"time":"7:30 PM","price":350,"availability":"Fast Filling"},{"time":"11:00 PM","price":300,"availability":"Available"}]}
            ]
        }
    ],
    "Bangalore": [
        {
            "title": "Gladiator II", "rating": "8.1", "duration": 148,
            "language": "English", "certification": "UA", "genres": ["Action","Drama","History"],
            "poster_emoji": "⚔️", "poster_gradient": "linear-gradient(135deg,#5C3317,#CD853F,#5C3317)",
            "description": "The sequel follows Lucius, the son of Maximus, who must fight as a gladiator in the Colosseum after the corrupt emperors murder his wife.",
            "director": "Ridley Scott", "cast": ["Paul Mescal","Pedro Pascal","Denzel Washington"],
            "release_date": "15 Nov 2024",
            "theatres": [
                {"id":"th_blr_1","name":"PVR IMAX Orion Mall","location":"Rajajinagar, Bangalore",
                 "features":["IMAX","Dolby Atmos","4K"],
                 "shows":[{"time":"10:00 AM","price":500,"availability":"Available"},{"time":"1:30 PM","price":500,"availability":"Fast Filling"},{"time":"5:00 PM","price":550,"availability":"Fast Filling"},{"time":"9:30 PM","price":500,"availability":"Available"}]},
                {"id":"th_blr_2","name":"Cinepolis Forum Mall","location":"Koramangala, Bangalore",
                 "features":["3D","Dolby"],
                 "shows":[{"time":"9:30 AM","price":300,"availability":"Available"},{"time":"2:00 PM","price":300,"availability":"Available"},{"time":"7:00 PM","price":320,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Interstellar 2", "rating": "9.1", "duration": 175,
            "language": "English", "certification": "U", "genres": ["Sci-Fi","Drama","Adventure"],
            "poster_emoji": "🌌", "poster_gradient": "linear-gradient(135deg,#000033,#003366,#000033)",
            "description": "A crew of astronauts travel through a newly discovered wormhole to discover if humanity can survive beyond our own galaxy.",
            "director": "Christopher Nolan", "cast": ["Matthew McConaughey","Anne Hathaway","Jessica Chastain"],
            "release_date": "5 Nov 2024",
            "theatres": [
                {"id":"th_blr_1","name":"PVR IMAX Orion Mall","location":"Rajajinagar, Bangalore",
                 "features":["IMAX","Dolby","ScreenX"],
                 "shows":[{"time":"9:00 AM","price":520,"availability":"Fast Filling"},{"time":"12:30 PM","price":520,"availability":"Fast Filling"},{"time":"4:00 PM","price":570,"availability":"Fast Filling"},{"time":"8:00 PM","price":570,"availability":"Available"}]},
                {"id":"th_blr_3","name":"Inox Garuda Mall","location":"MG Road, Bangalore",
                 "features":["4DX","3D"],
                 "shows":[{"time":"10:30 AM","price":380,"availability":"Available"},{"time":"3:00 PM","price":380,"availability":"Fast Filling"},{"time":"7:30 PM","price":400,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "The Dark Knight Returns", "rating": "9.0", "duration": 165,
            "language": "English", "certification": "UA", "genres": ["Action","Crime","Drama"],
            "poster_emoji": "🦇", "poster_gradient": "linear-gradient(135deg,#0a0a0a,#1a1a3e,#0a0a0a)",
            "description": "Bruce Wayne returns as Batman after years of retirement to face a new threat that tests his limits and the soul of Gotham City.",
            "director": "Matt Reeves", "cast": ["Robert Pattinson","Zoë Kravitz","Colin Farrell"],
            "release_date": "12 Mar 2025",
            "theatres": [
                {"id":"th_blr_4","name":"Multiplex Nexus Whitefield","location":"Whitefield, Bangalore",
                 "features":["IMAX","3D"],
                 "shows":[{"time":"11:00 AM","price":420,"availability":"Available"},{"time":"2:30 PM","price":420,"availability":"Available"},{"time":"6:00 PM","price":470,"availability":"Fast Filling"},{"time":"10:30 PM","price":420,"availability":"Available"}]}
            ]
        },
        {
            "title": "RRR 2", "rating": "8.6", "duration": 195,
            "language": "Telugu/Hindi", "certification": "UA", "genres": ["Action","Drama","History"],
            "poster_emoji": "🔥", "poster_gradient": "linear-gradient(135deg,#8B0000,#FF4500,#8B0000)",
            "description": "The legendary duo of Ram and Bheem return in a new epic saga set against the backdrop of India's independence movement.",
            "director": "SS Rajamouli", "cast": ["Ram Charan","NTR Jr.","Alia Bhatt"],
            "release_date": "15 Jan 2026",
            "theatres": [
                {"id":"th_blr_1","name":"PVR IMAX Orion Mall","location":"Rajajinagar, Bangalore",
                 "features":["IMAX","4DX","Dolby"],
                 "shows":[{"time":"9:00 AM","price":550,"availability":"Fast Filling"},{"time":"1:00 PM","price":550,"availability":"Fast Filling"},{"time":"5:00 PM","price":600,"availability":"Fast Filling"},{"time":"9:00 PM","price":600,"availability":"Available"}]}
            ]
        }
    ],
    "Hyderabad": [
        {
            "title": "Baahubali 3: The Legend Continues", "rating": "9.2", "duration": 210,
            "language": "Telugu/Hindi", "certification": "U", "genres": ["Action","Drama","Epic"],
            "poster_emoji": "👑", "poster_gradient": "linear-gradient(135deg,#4B3621,#FFD700,#4B3621)",
            "description": "The epic saga continues as the descendants of Mahishmati face a new enemy threatening the kingdom while uncovering hidden truths about their lineage.",
            "director": "SS Rajamouli", "cast": ["Prabhas","Rana Daggubati","Anushka Shetty"],
            "release_date": "10 Apr 2025",
            "theatres": [
                {"id":"th_hyd_1","name":"AMB Cinemas","location":"Gachibowli, Hyderabad",
                 "features":["IMAX","4DX","Dolby Atmos"],
                 "shows":[{"time":"9:00 AM","price":600,"availability":"Fast Filling"},{"time":"12:30 PM","price":600,"availability":"Fast Filling"},{"time":"4:00 PM","price":650,"availability":"Fast Filling"},{"time":"8:30 PM","price":700,"availability":"Fast Filling"}]},
                {"id":"th_hyd_2","name":"PVR Nexus Hyderabad","location":"Kukatpally, Hyderabad",
                 "features":["IMAX","3D"],
                 "shows":[{"time":"10:00 AM","price":420,"availability":"Available"},{"time":"2:00 PM","price":420,"availability":"Fast Filling"},{"time":"6:30 PM","price":450,"availability":"Fast Filling"},{"time":"10:30 PM","price":400,"availability":"Available"}]}
            ]
        },
        {
            "title": "Mission Impossible: Final Chapter", "rating": "8.3", "duration": 163,
            "language": "English", "certification": "UA", "genres": ["Action","Thriller","Adventure"],
            "poster_emoji": "💣", "poster_gradient": "linear-gradient(135deg,#1C1C1C,#B22222,#1C1C1C)",
            "description": "Ethan Hunt faces his most dangerous mission yet as he races against a rogue AI system that threatens global intelligence networks.",
            "director": "Christopher McQuarrie", "cast": ["Tom Cruise","Hayley Atwell","Simon Pegg"],
            "release_date": "23 May 2025",
            "theatres": [
                {"id":"th_hyd_3","name":"Inox GVK One","location":"Banjara Hills, Hyderabad",
                 "features":["Dolby Atmos","3D","Luxury"],
                 "shows":[{"time":"10:30 AM","price":360,"availability":"Available"},{"time":"2:30 PM","price":360,"availability":"Available"},{"time":"6:30 PM","price":400,"availability":"Fast Filling"},{"time":"10:00 PM","price":360,"availability":"Available"}]},
                {"id":"th_hyd_1","name":"AMB Cinemas","location":"Gachibowli, Hyderabad",
                 "features":["IMAX","4DX"],
                 "shows":[{"time":"9:30 AM","price":550,"availability":"Available"},{"time":"1:30 PM","price":550,"availability":"Fast Filling"},{"time":"5:30 PM","price":600,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Spider-Man: Across the Spider-Verse 2", "rating": "9.0", "duration": 155,
            "language": "English/Telugu", "certification": "U", "genres": ["Animation","Action","Adventure"],
            "poster_emoji": "🕷️", "poster_gradient": "linear-gradient(135deg,#1a0050,#CC0000,#1a0050)",
            "description": "Miles Morales returns in the next chapter of the Spider-Verse saga, traversing the multiverse with new allies and facing an impossible choice.",
            "director": "Joaquim Dos Santos", "cast": ["Shameik Moore","Hailee Steinfeld","Oscar Isaac"],
            "release_date": "2 Apr 2026",
            "theatres": [
                {"id":"th_hyd_4","name":"Cinepolis Hyderabad","location":"Ameerpet, Hyderabad",
                 "features":["3D","Dolby","IMAX"],
                 "shows":[{"time":"10:00 AM","price":320,"availability":"Available"},{"time":"1:00 PM","price":320,"availability":"Available"},{"time":"4:30 PM","price":350,"availability":"Fast Filling"},{"time":"8:00 PM","price":350,"availability":"Fast Filling"}]}
            ]
        }
    ],
    "Kochi": [
        {
            "title": "Manjummel Boys 2", "rating": "8.4", "duration": 145,
            "language": "Malayalam", "certification": "UA", "genres": ["Thriller","Adventure","Drama"],
            "poster_emoji": "🏔️", "poster_gradient": "linear-gradient(135deg,#006400,#228B22,#006400)",
            "description": "The friends reunite for another thrilling adventure that tests the bonds of friendship in the face of unimaginable danger.",
            "director": "Chidambaram S Poduval", "cast": ["Soubin Shahir","Sreenath Bhasi","Balu Varghese"],
            "release_date": "14 Feb 2025",
            "theatres": [
                {"id":"th_koc_1","name":"Cinepolis Lulu Mall","location":"Edappally, Kochi",
                 "features":["Dolby Atmos","3D","IMAX"],
                 "shows":[{"time":"10:00 AM","price":300,"availability":"Available"},{"time":"1:30 PM","price":300,"availability":"Fast Filling"},{"time":"5:00 PM","price":340,"availability":"Fast Filling"},{"time":"9:00 PM","price":300,"availability":"Available"}]},
                {"id":"th_koc_2","name":"PVR Gold Oberon Mall","location":"Edappally, Kochi",
                 "features":["Premium","Recliners"],
                 "shows":[{"time":"11:00 AM","price":450,"availability":"Available"},{"time":"3:00 PM","price":450,"availability":"Available"},{"time":"7:30 PM","price":500,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Avatar 3: Fire and Ash", "rating": "8.6", "duration": 195,
            "language": "English/Malayalam", "certification": "U", "genres": ["Sci-Fi","Adventure","Fantasy"],
            "poster_emoji": "🌿", "poster_gradient": "linear-gradient(135deg,#003300,#006633,#003300)",
            "description": "Jake Sully and Neytiri face a new threat as fire clans from Pandora's volcanic regions declare war on the forest and reef Na'vi.",
            "director": "James Cameron", "cast": ["Sam Worthington","Zoe Saldana","Sigourney Weaver"],
            "release_date": "19 Dec 2025",
            "theatres": [
                {"id":"th_koc_1","name":"Cinepolis Lulu Mall","location":"Edappally, Kochi",
                 "features":["IMAX","3D","Dolby"],
                 "shows":[{"time":"9:00 AM","price":400,"availability":"Fast Filling"},{"time":"12:30 PM","price":400,"availability":"Fast Filling"},{"time":"4:30 PM","price":450,"availability":"Fast Filling"},{"time":"9:30 PM","price":400,"availability":"Available"}]},
                {"id":"th_koc_3","name":"Regina Multiplex","location":"MG Road, Kochi",
                 "features":["3D","2D"],
                 "shows":[{"time":"10:30 AM","price":250,"availability":"Available"},{"time":"2:30 PM","price":250,"availability":"Available"},{"time":"7:00 PM","price":280,"availability":"Fast Filling"}]}
            ]
        },
        {
            "title": "Lucifer 3", "rating": "8.0", "duration": 158,
            "language": "Malayalam", "certification": "UA", "genres": ["Action","Thriller","Political"],
            "poster_emoji": "😈", "poster_gradient": "linear-gradient(135deg,#1a0020,#6B0080,#1a0020)",
            "description": "Stephen Nedumpally returns in the final chapter of the Empuraan trilogy, bringing his war against corruption to a global stage.",
            "director": "Prithviraj Sukumaran", "cast": ["Mohanlal","Prithviraj","Manju Warrier"],
            "release_date": "1 Jan 2026",
            "theatres": [
                {"id":"th_koc_4","name":"Inox Sapphire Mall","location":"Thrippunithura, Kochi",
                 "features":["Dolby Atmos","DBOX"],
                 "shows":[{"time":"10:00 AM","price":280,"availability":"Available"},{"time":"1:30 PM","price":280,"availability":"Fast Filling"},{"time":"5:30 PM","price":320,"availability":"Fast Filling"},{"time":"9:30 PM","price":280,"availability":"Available"}]}
            ]
        }
    ]
}

def seed_movies():
    if db.movies.count_documents({}) == 0:
        for city, movies in MOVIES_DATA.items():
            for m in movies:
                doc = m.copy()
                doc['city'] = city
                db.movies.insert_one(doc)
        print("Movies seeded successfully.")

def serialize(doc):
    doc['_id'] = str(doc['_id'])
    return doc

@app.route('/movies/<city>')
def get_movies(city):
    movies = list(db.movies.find({'city': city}))
    return jsonify([serialize(m) for m in movies])

@app.route('/movie/<movie_id>')
def get_movie(movie_id):
    try:
        from bson import ObjectId as OID
        movie = db.movies.find_one({'_id': OID(movie_id)})
        if movie:
            return jsonify(serialize(movie))
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'movie-service'})

with app.app_context():
    seed_movies()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)

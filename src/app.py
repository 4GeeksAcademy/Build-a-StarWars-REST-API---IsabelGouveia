"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, session
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token


app = Flask(__name__)
jwt = JWTManager(app)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# Route to get information about all characters (people)
@app.route('/people', methods=['GET'])
def get_people():
    characters = Character.query.all()
    results = [character.serialize() for character in characters]
    return jsonify(results), 200

# Route to get information about a specific character (people)
@app.route('/people/<int:character_id>', methods=['GET'])
def get_character(character_id):
    character = Character.query.get(character_id)
    if character:
        return jsonify(character.serialize()), 200

# Route to get information about all planets 
@app.route('/planet', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    results = [planet.serialize() for planet in planets]
    return jsonify(results), 200

# Route to get information about a specific planet
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet:
        return jsonify(planet.serialize()), 200
    
# Route to get information about all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    results = [user.serialize() for user in users]
    
    access_token = create_access_token(identity=get_jwt_identity())
    response_body = {
        "access_token": access_token,
        "users": results
    }
    return jsonify(response_body), 200

# Route to get all the favorites that belong to a current user
@app.route('/users/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    user_id = get_jwt_identity()

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    serialized_favorites = [favorite.serialize() for favorite in favorites]

    return jsonify(serialized_favorites), 200

# Route [POST] /favorite/planet/<int:planet_id> Add a new favorite planet to the current user with the planet id = planet_id
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
@jwt_required()
def add_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"message": "User not authenticated"}), 401
    
    
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"message": "Planet not found"}), 404
    
    
    valid_favorite = Favorite.query.filter_by(user_id=user_id, item_type='planet', item_id=planet_id).first()
    if valid_favorite:
        return jsonify({"message": "Planet is already a favorite"}), 400
    
    new_favorite = Favorite(user_id=user_id, item_type='planet', item_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    
    return jsonify({"message": "Favorite planet added"}), 201

# Route [POST] /favorite/people/<int:people_id> Add new favorite people to the current user with the people id = people_id
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
@jwt_required()
def add_favorite_people(people_id):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"message": "User not authenticated"}), 401
    
    
    character = Character.query.get(people_id)
    if character is None:
        return jsonify({"message": "Character not found"}), 404
    
    
    valid_favorite = Favorite.query.filter_by(user_id=user_id, item_type='character', item_id=people_id).first()
    if valid_favorite:
        return jsonify({"message": "Character is already a favorite"}), 400
    
    new_favorite = Favorite(user_id=user_id, item_type='character', item_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    
    return jsonify({"message": "Favorite character added"}), 201



# Route to delete favorite planet with the id = planet_id
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"message": "User not authenticated"}), 401

    favorite = Favorite.query.filter_by(user_id=user_id, item_type='planet', item_id=planet_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"message": "Favorite planet deleted"}), 200
    else:
        return jsonify({"message": "Favorite planet not found"}), 404

# Route to delete favorite character with the id = people_id
@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_character(people_id):
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"message": "User not authenticated"}), 401

    favorite = Favorite.query.filter_by(user_id=user_id, item_type='character', item_id=people_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"message": "Favorite character deleted"}), 200
    else:
        return jsonify({"message": "Favorite character not found"}), 404


@app.route('/token', methods=['GET'])
@jwt_required()
def get_token():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

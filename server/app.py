from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
import os
from models import db, Restaurant, Pizza, RestaurantPizza

# Set up the database path and Flask app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# Set up Flask-Migrate for database migrations
migrate = Migrate(app, db)
db.init_app(app)

# GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    
    restaurant_list = []
    for restaurant in restaurants:
        restaurant_list.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'restaurant_pizzas': [
                {
                    'id': restaurant_pizza.id,
                    'price': restaurant_pizza.price,
                    'pizza': {
                        'id': restaurant_pizza.pizza.id,
                        'name': restaurant_pizza.pizza.name,
                        'ingredients': restaurant_pizza.pizza.ingredients
                    },
                    'restaurant_id': restaurant_pizza.restaurant_id,
                    'pizza_id': restaurant_pizza.pizza_id
                } for restaurant_pizza in restaurant.restaurant_pizzas
            ]
        })

    return jsonify(restaurant_list)

# GET /restaurants/int:id
@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant_by_id(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    restaurant_data = {
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address,
        'restaurant_pizzas': [
            {
                'id': restaurant_pizza.id,
                'price': restaurant_pizza.price,
                'pizza': {
                    'id': restaurant_pizza.pizza.id,
                    'name': restaurant_pizza.pizza.name,
                    'ingredients': restaurant_pizza.pizza.ingredients
                },
                'restaurant_id': restaurant_pizza.restaurant_id,
                'pizza_id': restaurant_pizza.pizza_id
            } for restaurant_pizza in restaurant.restaurant_pizzas
        ]
    }

    return jsonify(restaurant_data), 200

# DELETE /restaurants/int:id
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    # Delete associated restaurant_pizzas first (if cascade is not set)
    for restaurant_pizza in restaurant.restaurant_pizzas:
        db.session.delete(restaurant_pizza)

    db.session.delete(restaurant)
    db.session.commit()

    return jsonify({}), 204

# GET /pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()

    pizza_list = []
    for pizza in pizzas:
        pizza_list.append({
            'id': pizza.id,
            'name': pizza.name,
            'ingredients': pizza.ingredients
        })

    return jsonify(pizza_list), 200

# POST /restaurant_pizzas
@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    # Ensure the required fields are in the request body
    if not data or 'price' not in data or 'pizza_id' not in data or 'restaurant_id' not in data:
        return jsonify({"errors": ["validation errors"]}), 400

    price = data['price']
    pizza_id = data['pizza_id']
    restaurant_id = data['restaurant_id']

    # Check if price is valid
    if price < 1 or price > 30:
        return jsonify({"errors": ["Price must be between 1 and 30"]}), 400

    # Ensure the pizza and restaurant exist
    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)
    if not pizza or not restaurant:
        return jsonify({"errors": ["Invalid pizza_id or restaurant_id"]}), 400

    # Create the RestaurantPizza
    restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
    db.session.add(restaurant_pizza)
    db.session.commit()

    # Return the new RestaurantPizza data
    return jsonify({
        'id': restaurant_pizza.id,
        'price': restaurant_pizza.price,
        'pizza': {
            'id': pizza.id,
            'name': pizza.name,
            'ingredients': pizza.ingredients
        },
        'restaurant': {
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address
        },
        'restaurant_id': restaurant_pizza.restaurant_id,
        'pizza_id': restaurant_pizza.pizza_id
    }), 201

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource, abort
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

# Define serialization rules to limit recursion depth
def serialize_restaurant(restaurant):
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "address": restaurant.address
    }

def serialize_pizza(pizza):
    return {
        "id": pizza.id,
        "name": pizza.name,
        "ingredients": pizza.ingredients
    }

def serialize_restaurant_pizza(restaurant_pizza):
    return {
        "id": restaurant_pizza.id,
        "restaurant_id": restaurant_pizza.restaurant_id,
        "restaurant": serialize_restaurant(restaurant_pizza.restaurant),
        "pizza_id": restaurant_pizza.pizza_id,
        "pizza": serialize_pizza(restaurant_pizza.pizza),
        "price": restaurant_pizza.price
    }


class RestaurantListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return jsonify([serialize_restaurant(restaurant) for restaurant in restaurants])


class RestaurantResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            abort(404, error="Restaurant not found")
        return jsonify({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [serialize_restaurant_pizza(rp) for rp in restaurant.restaurant_pizzas]
        })

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if not restaurant:
            abort(404, error="Restaurant not found")
        # Delete associated restaurant pizzas
        RestaurantPizza.query.filter_by(restaurant_id=id).delete()
        db.session.delete(restaurant)
        db.session.commit()
        return make_response("", 204)


class PizzaListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return jsonify([serialize_pizza(pizza) for pizza in pizzas])


class RestaurantPizzaResource(Resource):
    def post(self):
        data = request.get_json()
        price = data.get('price')
        pizza_id = data.get('pizza_id')
        restaurant_id = data.get('restaurant_id')

        # Validate inputs
        if not (price and 1 <= price <= 30):
            return jsonify({"errors": ["Validation error: Price must be between 1 and 30"]}), 400

        # Check if pizza with given pizza_id exists
        pizza = Pizza.query.get(pizza_id)
        if not pizza:
            abort(400, error=f"Pizza with id {pizza_id} does not exist")

        # Check if restaurant with given restaurant_id exists
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            abort(400, error=f"Restaurant with id {restaurant_id} does not exist")

        # Create new RestaurantPizza entry
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        return jsonify(serialize_restaurant_pizza(new_restaurant_pizza)), 201  # Return 201 Created


# Routes
api.add_resource(RestaurantListResource, '/restaurants')
api.add_resource(RestaurantResource, '/restaurants/<int:id>')
api.add_resource(PizzaListResource, '/pizzas')
api.add_resource(RestaurantPizzaResource, '/restaurant_pizzas')

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

if __name__ == "__main__":
    app.run(port=5555, debug=True)
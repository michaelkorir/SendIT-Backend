from flask import Flask, make_response, request, jsonify, abort, render_template
from flask_migrate import Migrate
from flask import jsonify
from flask_restful import  Api, Resource
from flask_cors import  CORS
from flask_jwt_extended import JWTManager, current_user, jwt_required, get_jwt_identity
from werkzeug.exceptions import NotFound
from models import db, User, Parcel, TokenBlocklist
from auth import auth_bp

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = b'\xb2\xd3B\xb9 \xab\xc0By\x13\x10\x84\xb7M!\x11'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SENDIT.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_SECRET_KEY'] = 'senditadmindashboard'

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

CORS(app)
jwt = JWTManager()
jwt.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

@app.errorhandler(NotFound)
def handle_not_found(e):
    response = make_response("NotFound: The requested resource not found", 404)
    return response

class ParcelsList(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user_role = get_user_role_by_id(current_user_id)
        
        if user_role != 'admin':
            return {"message": "You are not authorized to access this resource"}, 403

        parcels = Parcel.query.all()
        serialized_parcels = [parcel.serialize() for parcel in parcels]
        return jsonify(serialized_parcels)
    

api.add_resource(ParcelsList, "/parcels")

def get_user_role_by_id(user_id):
    user = User.query.get(user_id)
    if user:
        return user.role
    else:
        return None

if __name__ == '__main__':
    app.run(port=5555, debug=True)

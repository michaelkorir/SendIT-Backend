from datetime import timedelta
from mailbox import Message
# import mailbox
from flask_mail import Mail
from flask import Flask, current_app, make_response, request, jsonify, abort, render_template
from flask_migrate import Migrate
from flask import jsonify
from flask_restful import  Api, Resource, reqparse
from flask_cors import  CORS
from flask_jwt_extended import JWTManager, current_user, jwt_required, get_jwt_identity
from sqlalchemy import func
from werkzeug.exceptions import NotFound
from models import db, User, Parcel, TokenBlocklist
from auth import auth_bp

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = b'\xb2\xd3B\xb9 \xab\xc0By\x13\x10\x84\xb7M!\x11'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SENDIT.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_SECRET_KEY'] = 'senditadmindashboard'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=5)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'senditkenya@gmail.com'
app.config['MAIL_PASSWORD'] = 'ibvjuqdlpemtiaqf'
app.config['MAIL_DEFAULT_SENDER'] = 'senditkenya@gmail.com'
mail = Mail(app)

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
    
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        # Check if the user is an admin
        if current_user.role == 'admin':
            return {"message": "Admins are not allowed to create parcels"}, 403

        data = request.get_json()

        # Check if all required fields are filled
        required_fields = ['name', 'description', 'weight', 'pickup_location', 'destination_location']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {"message": f"Missing required fields: {', '.join(missing_fields)}"}, 400

        new_parcel = Parcel(
            user_id=current_user_id,
            name=data['name'],
            description=data['description'],
            weight=data['weight'],
            pickup_location=data['pickup_location'],
            destination_location=data['destination_location']
        )

        db.session.add(new_parcel)
        db.session.commit()

        return {"message": "Parcel created successfully"}, 201
    
api.add_resource(ParcelsList, "/parcels")

def get_user_role_by_id(user_id):
    user = User.query.get(user_id)
    if user:
        return user.role
    else:
        return None


class ParcelStatus(Resource):
    @jwt_required()
    def put(self, tracking_number):
        current_user_id = get_jwt_identity()
        user_role = get_user_role_by_id(current_user_id)
        
        if user_role != 'admin':
            return {"message": "You are not authorized to perform this action"}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=True, help='New status of the parcel is required')
        args = parser.parse_args()

        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()
        if parcel:
            if parcel.status.lower() == 'cancelled':
                return ({"message": "Cannot update status of a cancelled parcel"}), 400
            previous_status = parcel.status
            parcel.status = args['status']
            db.session.commit()  # Commit changes to the database
            
            # Send email notification to user
            send_email_notification(parcel.user, parcel.tracking_number, previous_status, args['status'])
            
            return ({"message": "Parcel status updated successfully"})
        else:
            return {"message": "Parcel not found"}, 404

def send_email_notification(user, tracking_number, previous_status, new_status):
    subject = "Parcel Status Update"
    body = f"Your parcel with tracking number {tracking_number} has been updated.\nPrevious status: {previous_status}\nNew status: {new_status}"
    
    mail.send_message(subject=subject, recipients=[user.email], body=body)


api.add_resource(ParcelStatus, "/parcel/status/<string:tracking_number>")


class ParcelLocation(Resource):
    @jwt_required()
    def put(self, tracking_number):
        current_user_id = get_jwt_identity()
        user_role = get_user_role_by_id(current_user_id)
        
        if user_role != 'admin':
            return {"message": "You are not authorized to perform this action"}, 403

        parser = reqparse.RequestParser()
        parser.add_argument('present_location', type=str, required=True, help='New location of the parcel is required')
        args = parser.parse_args()

        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()
        if parcel:
            parcel.present_location = args['present_location']
            db.session.commit()  # Commit changes to the database
            return ({"message": "Parcel location updated successfully"})
        else:
            return {"message": "Parcel not found"}, 404


api.add_resource(ParcelLocation, "/parcel/location/<string:tracking_number>")

class ParcelDestination(Resource):
    @jwt_required()
    def put(self, tracking_number):
        current_user_id = get_jwt_identity()
        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()

        # Do parcel exist
        if not parcel:
            return {"message": "Parcel not found"}, 404

        # is user authorized to modify this parcel
        if parcel.user_id != current_user_id:
            return {"message": "You are not authorized to modify this parcel"}, 403

        # Check if the parcel's status is delivered
        if parcel.status == 'delivered':
            return {"message": "Parcel has already been delivered, cannot modify destination"}, 400

        data = request.get_json()

        # is new destination location provided
        if 'destination_location' not in data:
            return {"message": "New destination location is required"}, 400

        # Update the destination location
        parcel.destination_location = data['destination_location']
        db.session.commit()

        return {"message": "Parcel destination updated successfully"}, 200
    
api.add_resource(ParcelDestination, '/parcel/destination/<string:tracking_number>')

class CancelParcel(Resource):
    @jwt_required()
    def put(self, tracking_number):
        current_user_id = get_jwt_identity()
        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()

        if parcel is None:
            return ({"message": "Parcel not found"}), 404

        # is user authorized to cancel this parcel
        if parcel.user_id != current_user_id:
            return ({"message": "You are not authorized to cancel this parcel"}), 403

        # Check if the parcel's status is not delivered
        if parcel.status.lower() != 'delivered':
            # Cancel the parcel (update status)
            parcel.status = 'cancelled'
            db.session.commit()
            
            return ({"message": "Parcel cancelled successfully"}), 200
        else:
            # response indicating failure due to delivered status
            return ({"message": "Cannot cancel a delivered parcel"}), 400


api.add_resource(CancelParcel, '/parcel/cancel/<string:tracking_number>')


if __name__ == '__main__':
    app.run(port=5555, debug=True)

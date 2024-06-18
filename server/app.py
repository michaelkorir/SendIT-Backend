import os 
from dotenv import load_dotenv
load_dotenv()
from datetime import timedelta
from mailbox import Message
from flask_mail import Mail
from flask import Flask, current_app, make_response, request, jsonify, abort, render_template
from flask_migrate import Migrate
from flask import jsonify
from flask_restful import  Api, Resource, reqparse
from flask_cors import  CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import func
from werkzeug.exceptions import NotFound
from models import db, User, Parcel, TokenBlocklist
from auth import auth_bp
# from flask_admin import Admin
# from flask_admin.contrib.sqla import ModelView
# from views import UserAdminView, ParcelAdminView


app = Flask(__name__)
# admin = Admin(app, name='SendIT Admin Panel', template_mode='bootstrap4')

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SENDIT.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_SECRET_KEY'] = os.getenv('ADMIN_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=5)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
mail = Mail(app)

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

CORS(app)
jwt = JWTManager()
jwt.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')

# admin.add_view(UserAdminView(User, db.session))
# admin.add_view(ParcelAdminView(Parcel, db.session))

#check if the jwt is revoked
@jwt.token_in_blocklist_loader 
def token_in_blocklist(jwt_header,jwt_data):
    jti = jwt_data['jti']

    token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()
    return token is not None

@app.errorhandler(NotFound)
def handle_not_found(e):
    response = make_response("NotFound: The requested resource not found", 404)
    return response

@app.route("/")
def home():
    return "<h1>Welcome to SendIT Courrier</h1>"

class Parcels(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user_role = get_user_role_by_id(current_user_id)
        if user_role != 'user':
            return {"message": "Admins do not have parcels"}, 403

        parcels = Parcel.query.filter_by(user_id=current_user_id).all()
        
        serialized_parcels = [parcel.serialize() for parcel in parcels]
        return jsonify(serialized_parcels)
    
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if current_user.role == 'admin':
            return {"message": "Admins are not allowed to create parcels"}, 403

        data = request.get_json()

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
            destination_location=data['destination_location'],
            notifications=data.get('notifications')
        )

        db.session.add(new_parcel)
        db.session.commit()
        send_post_notifications(current_user, new_parcel.tracking_number, new_parcel.notifications)

        return {"message": "Parcel created successfully"}, 201

def send_post_notifications(user, tracking_number, notifications):
    subject = "New Parcel Created"
    body = f" Hi{notifications} \n \n Your parcel tracking number is {tracking_number}.\n \n Kind Regards \n \n SendIT Kenya."
    
    mail.send_message(subject=subject, recipients=[user.email], body=body)

        
api.add_resource(Parcels, "/parcel")

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
            db.session.commit() 
            
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
        parser.add_argument('current_location', type=str, required=True, help='Current location of the parcel is required')
        args = parser.parse_args()

        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()
        if parcel:
            parcel.present_location = args['current_location']
            db.session.commit()  # Commit changes to the database
            return ({"message": "Parcel location updated successfully"})
        else:
            return {"message": "Parcel not found"}, 404


api.add_resource(ParcelLocation, "/parcel/location/<string:tracking_number>")

class ParcelDestination(Resource):
    @jwt_required()
    def patch(self, tracking_number):
        current_user_id = get_jwt_identity()
        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()

        if not parcel:
            return {"message": "Parcel not found"}, 404

        if parcel.user_id != current_user_id:
            return {"message": "You are not authorized to modify this parcel"}, 403

        if parcel.status == 'delivered':
            return {"message": "Parcel has already been delivered, cannot modify destination"}, 400

        data = request.get_json()

        if 'new_destination' not in data:
            return {"message": "New destination location is required"}, 400

        parcel.destination_location = data['new_destination']
        db.session.commit()

        return {"message": "Parcel destination updated successfully"}, 200
    
api.add_resource(ParcelDestination, '/parcel/destination/<string:tracking_number>')

class CancelParcel(Resource):
    @jwt_required()
    def put(self, tracking_number):
        current_user_id = get_jwt_identity()
        parcel = Parcel.query.filter_by(tracking_number=tracking_number.upper()).first()

        if parcel is None:
            return {"message": "Parcel not found"}, 404

        if parcel.user_id != current_user_id:
            return {"message": "You are not authorized to cancel this parcel"}, 403

        if parcel.status.lower() == 'delivered':
            return {"message": "Cannot cancel a delivered parcel"}, 400

        parcel.status = 'Canceled'
        db.session.commit()
            
        return {"message": "Parcel cancelled successfully"}, 200

api.add_resource(CancelParcel, '/parcel/cancel/<string:tracking_number>')



# if __name__  =="__main__":
#     app.run (port =5555, debug =True)
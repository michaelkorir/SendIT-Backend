
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jwt_identity
from models import User, TokenBlocklist, db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    secret_key = data.get('secret_key')

    if not username or not email or not password or not confirm_password:
        return jsonify({'message': 'Missing username, email, password, or confirm_password'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Password and confirm password do not match'}), 400

    # Determine user role based on the admin secret key
    role = 'user'
    admin_secret_key = current_app.config.get('ADMIN_SECRET_KEY')
    if secret_key == admin_secret_key:
        role = 'admin'
    elif secret_key is not None:
        return jsonify({'message': 'Invalid secret key'}), 401

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    user = User.register(username, email, password, role=role)
    if not user:
        return jsonify({'message': 'Failed to create user'}), 500

    access_token = create_access_token(identity=user.id)
    return jsonify({'message': 'User created successfully', 'access_token': access_token}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id)
    
    return jsonify({'message': 'Logged in successfully', 'access_token': access_token}), 200


@auth_bp.get('/logout')
@jwt_required(verify_type=False) 
def logout_user():
    jwt = get_jwt()

    jti = jwt['jti']

    token_blocklist = TokenBlocklist(jti=jti)

    db.session.add(token_blocklist)
    db.session.commit()

    return jsonify({"Message" : "Logged Out Successfully"}),200
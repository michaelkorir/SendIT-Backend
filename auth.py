
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    secret_key = data.get('secret_key')

    if not username or not email or not password:
        return jsonify({'message': 'Missing username, email, or password'}), 400

    # Determine user role based on the admin secret key
    role = 'user'
    admin_secret_key = current_app.config.get('ADMIN_SECRET_KEY')
    if secret_key == admin_secret_key:
        role = 'admin'
    elif secret_key is not None:
        return jsonify({'message': 'Invalid secret key'}), 401

    # Check if the user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400

    # Create a new user
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



@auth_bp.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt_identity()
    if jti:
        revoked_token = TokenBlocklist(jti=jti)
        revoked_token.add()
        return jsonify({'message': 'Successfully logged out'}), 200
    else:
        return jsonify({'message': 'Invalid user'}), 400

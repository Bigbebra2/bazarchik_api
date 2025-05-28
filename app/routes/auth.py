from flask import Blueprint, request, jsonify
from ..extensions import db, jwt
from ..models import User, Profile
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import current_user, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    name = request.json.get('name')
    surname = request.json.get('surname')
    age =  request.json.get('age')
    email = request.json.get('email')
    password = request.json.get('password')
    password2 = request.json.get('password2')

    # Field validations
    if not all([name, surname, age, email, password, password2]):
        return jsonify(msg='Missing some fields'), 400
    elif len(name.strip()) < 2 or any(not el.isalpha() for el in name):
        return jsonify(msg='The name field must consist of at least 2 characters and contain only letters')
    elif len(surname.strip()) < 2 or any(not el.isalpha() for el in surname):
        return jsonify(msg='The surname field must consist of at least 2 characters and contain only letters')
    elif password != password2:
        return jsonify(msg='Passwords do not match')
    elif len(password.strip()) < 4:
        return jsonify(msg='password must contain at least 5 characters')

    # Trying to register new user
    try:
        user = User.query.filter_by(email=email).one_or_none()
        if not user:
            hash_ = generate_password_hash(password)
            new_user = User(email=email, password=hash_)
            db.session.add(new_user)
            db.session.flush()

            new_profile = Profile(name=name, surname=surname, age=age, user_id=new_user.id)
            db.session.add(new_profile)
            db.session.commit()
            return jsonify(msg='User created successfully'), 201
        else:
            return jsonify(msg='A user with this email already exists'), 400
    except Exception as e:
        db.session.rollback()
        print(f'Error while registering user: {e}')
        return jsonify(msg='server error while registering user'), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')

    if not email or not password:
        return jsonify(msg='Missing password or email field'), 400

    user = User.query.filter_by(email=email).one_or_none()
    if not user or not check_password_hash(user.password, password):
        return jsonify(msg='Wrong email or password'), 401
    else:
        access_token = create_access_token(identity=str(user.id), fresh=True, expires_delta=timedelta(hours=1))
        refresh_token = create_refresh_token(identity=str(user.id), expires_delta=timedelta(days=7))
        return jsonify(access_token=access_token, refresh_token=refresh_token, user_id=user.id), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True, locations=['json'])
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)


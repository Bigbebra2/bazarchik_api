from flask import Blueprint, jsonify, request, send_file
from ..extensions import jwt, db
from ..models import User, Profile
from flask_jwt_extended import jwt_required, current_user, get_jwt
from  ..extensions import ALLOWED_EXTENSIONS, redis_blocklist
import os
from werkzeug.utils import secure_filename
import json


profile_bp = Blueprint('profile', __name__)

MAX_IMAGE_SIZE = (1024 * 1024) * 4

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return redis_blocklist.get(jti) is not None

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    id = jwt_data["sub"]
    return User.query.get(id)

@profile_bp.route('/my-profile')
@jwt_required()
def my_profile():
    pr = current_user.profile
    return jsonify(my_profile={
        'name': pr.name,
        'surname': pr.surname,
        'age': pr.age,
        'bio': pr.bio,
        'phone_number': pr.phone_number,
        'location': pr.location,
        'img_path': pr.img_path,
        'user_id': pr.user_id,
        'email': current_user.email,
        'reg_time': current_user.reg_datetime,
        'posts_id': [p.id for p in current_user.posts]
    }), 200

@profile_bp.route('/<int:id>')
def profile(id):
    pr = Profile.query.filter_by(user_id=id).one_or_none()
    if not pr:
        return jsonify(msg='User does not exists'), 400

    return jsonify(profile={
        'name': pr.name,
        'surname': pr.surname,
        'age': pr.age,
        'bio': pr.bio,
        'phone_number': pr.phone_number,
        'location': pr.location,
        'img_path': pr.img_path,
        'user_id': pr.user_id,
        'email': pr.user.email,
        'reg_time': pr.user.reg_datetime
    }), 200

@profile_bp.route('/my-profile/upload-ava', methods=['POST'])
@jwt_required()
def upload_ava():
    image = request.files.getlist('ava')[0]
    print(image.filename)

    if len(request.files.getlist('ava')) != 1:
        return jsonify(msg='Only 1 image needed'), 400
    if not image or not image.filename:
        return jsonify(msg='No image passed or wrong filename')

    ext = os.path.splitext(secure_filename(image.filename))[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify(msg='Unsupported file extension'), 400

    image.seek(0, os.SEEK_END)
    size_bytes = image.tell()
    image.seek(0)
    if size_bytes > MAX_IMAGE_SIZE:
        return jsonify(msg=f'File {image.filename} exceeds {MAX_IMAGE_SIZE / (1024*1024)} MB'), 400

    prev_path = current_user.profile.img_path
    if prev_path and os.path.isfile(os.path.join(os.getcwd(), prev_path)):
        os.remove(prev_path)

    path = os.path.join('uploads', 'avas', f'{current_user.id}_ava{ext}')

    image.save(os.path.join(os.getcwd(), path))
    current_user.profile.img_path = path
    db.session.commit()
    return jsonify(msg='Ava uploaded successfully'), 200

@profile_bp.route('/get-image/<path:f_path>')
def get_image(f_path: str):
    if not f_path.startswith(('uploads/', 'uploads\\')):
        return jsonify(msg='Wrong directory'), 404

    full_path = os.path.join(os.getcwd(), f_path)

    if os.path.isfile(full_path):
        return send_file(full_path)

    return jsonify(msg='File not found'), 404

@profile_bp.route('/my-profile/set-data', methods=['PUT'])
@jwt_required()
def change_profile_data():
    if not request.is_json:
        return jsonify(msg="Invalid or missing JSON"), 400

    data = request.get_json()
    allowed_fields = ('name', 'surname', 'age', 'bio', 'phone_number', 'location')
    errors = {}

    try:
        for key in allowed_fields:
            if key in data and data[key] != 'null':
                value = data[key]

                if key == 'age':
                    try:
                        value = int(value)
                        if value <= 0 or value > 150:
                            errors[key] = 'Age must be between 1 and 150'
                    except (ValueError, TypeError):
                        errors[key] = 'Age must be an integer'
                elif key in ('name', 'surname') and not isinstance(value, str):
                    errors[key] = 'Must be a string'
                elif key == 'phone_number' and (not isinstance(value, str) or len(value) < 7):
                    errors[key] = 'Invalid phone number'

                if key not in errors:
                    setattr(current_user.profile, key, value)

        print(errors)
        if errors:
            db.session.rollback()
            return jsonify(errors=errors), 400

        db.session.commit()
        return jsonify(msg='Profile updated successfully')

    except Exception as e:
        db.session.rollback()
        print(f'Error while changing user info: {e}')
        return jsonify(msg='An unexpected error occurred'), 500

@profile_bp.route('/delete-profile', methods=['DELETE'])
@jwt_required(fresh=True)
def delete_profile():
    identity = get_jwt()["jti"]
    redis_blocklist.set(identity, "revoked", ex=3600)

    db.session.delete(current_user)
    db.session.commit()
    return jsonify(msg="Your account has been deleted."), 200

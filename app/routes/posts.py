from flask import Blueprint, request, jsonify, send_file
from ..extensions import db, jwt, ALLOWED_EXTENSIONS
from ..models import User, Post
from flask_jwt_extended import jwt_required, current_user
from werkzeug.utils import secure_filename
from ..utils.file_load import clear_folder
from sqlalchemy import or_
from math import ceil
import os
import shutil


posts_bp = Blueprint('posts', __name__)

MAX_IMAGE_SIZE = (1024 * 1024) * 2
MAX_IMAGES = 4
MAX_TOTAL_SIZE = MAX_IMAGE_SIZE * MAX_IMAGES


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    id = jwt_data["sub"]
    return User.query.get(id)

@posts_bp.route('/create-post', methods=['POST'])
@jwt_required()
def create_post():
    title = request.form.get('title')
    price = request.form.get('price')
    description = request.form.get('description')

    # Basic validation
    print(title, price, description)
    if not all([title, price, description]):
        return jsonify(msg='Missing some fields'), 400
    elif len(title.strip()) < 4:
        return jsonify(msg='The title must be at least 5 characters long'), 400
    elif len(description.strip()) < 10:
        return jsonify(msg='The description must be at least 10 characters long'), 400

    # Individual price validation
    try:
        price = float(price)
        if price <= 0:
            return jsonify(msg='The price must be positive'), 400
    except ValueError:
        return jsonify(msg='Invalid price format'), 400

    # Creating new post
    try:
        new_post = Post(title=title, price=price, description=description, creator_id=current_user.id)
        db.session.add(new_post)
        db.session.flush()

        # Defining the post directory
        path = os.path.join('uploads', 'posts', str(new_post.id))
        os.makedirs(path, exist_ok=True)
        new_post.img_path = path

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Error creating post: {e}')
        return jsonify(msg='Error creating post'), 500

    saved_files = []
    images = request.files.getlist('files')[:MAX_IMAGES]
    total_size = 0

    for idx, img in enumerate(images, start=1):
        if img and img.filename:
            filename = secure_filename(img.filename)
            ext = os.path.splitext(filename)[1].lower()

            img.seek(0, os.SEEK_END)
            size_bytes = img.tell()
            img.seek(0)

            if ext not in ALLOWED_EXTENSIONS:
                clear_folder(path)
                return jsonify(msg=f'Unsupported file extension: {ext}'), 400
            if size_bytes > MAX_IMAGE_SIZE:
                clear_folder(path)
                return jsonify(msg=f'File {filename} exceeds {MAX_IMAGE_SIZE / (1024*1024)} MB'), 400

            saved_name = f"post_image{idx}{ext}"
            saved_path = os.path.join(path, saved_name)
            img.save(saved_path)
            saved_files.append(saved_name)
            total_size += size_bytes

    if total_size > MAX_TOTAL_SIZE:
        clear_folder(path)
        return jsonify(msg=f'Total size of images exceeds {MAX_TOTAL_SIZE / (1024*1024)} MB'), 400

    db.session.commit()
    return jsonify(
        msg='Post created successfully',
        post_id=new_post.id,
        images=saved_files
    ), 201


@posts_bp.route('/page/<int:page>')
def get_posts(page):
    posts = []
    try:
        posts = Post.query.order_by(Post.creation_date.desc()).offset((page-1) * 10).limit(10).all()
    except Exception as e:
        print(f'Error while getting posts: {e}')

    if not posts:
        return jsonify(msg='No posts on this page'), 400

    response = []

    for p in posts:
        data = {'id': p.id,
                     'title': p.title,
                     'price': p.price,
                     'location': p.creator.profile.location,
                     'time':  p.creation_date,
                     'page': page,
                     'description': p.description
                     }
        image = os.listdir(p.img_path)

        if image:
            data.update({'image': os.path.join(p.img_path, os.listdir(p.img_path)[0])})
        else:
            data.update({'image': None})

        response.append(data)

    return jsonify(response)

@posts_bp.route('/<int:id>')
def get_post_by_id(id):
    post = Post.query.filter_by(id=id).one_or_none()

    if not post:
        return jsonify(msg='Post with this id does not exists'), 400

    path = post.img_path
    images = [os.path.join(path, f) for f in os.listdir(path) if f[f.rfind('.'):] in ALLOWED_EXTENSIONS]

    return jsonify(post={
        'id': post.id,
        'creator_id': post.creator.id,
        'title': post.title,
        'description': post.description,
        'price': post.price,
        'time': post.creation_date,
        'img_path': images
    })

@posts_bp.route('/search/<string:search_word>/<int:page>')
def get_searched_posts(search_word, page):
    words = tuple(map(str.strip, search_word.split()))
    if not words:
        return jsonify({"msg": "search data can't be empty"}), 400

    query = Post.query.filter(
        or_(*(Post.title.ilike(f"%{kw}%") for kw in words))
    ).order_by(Post.creation_date.desc())

    total_pages = ceil(query.count() / 10)
    posts = query.offset((page - 1) * 10).limit(10).all()

    res = [{
        'id': p.id,
        'title': p.title,
        'time': p.creation_date,
        'location': p.creator.profile.location,
        'creator_id': p.creator_id,
        'price': float(p.price),
        'img_path': [os.path.join(p.img_path, f) for f in os.listdir(p.img_path) if f[f.rfind('.'):] in ALLOWED_EXTENSIONS],
        'description': p.description
    } for p in posts]

    if not res:
        return jsonify(msg='No post on this search'), 400

    return jsonify(total_pages=total_pages, posts=res)

@posts_bp.route('/get-image/<path:f_path>')
def get_image(f_path: str):
    if not f_path.startswith(('uploads/', 'uploads\\')):
        return jsonify(msg='Wrong directory'), 404

    full_path = os.path.join(os.getcwd(), f_path)

    if os.path.isfile(full_path):
        return send_file(full_path)

    return jsonify(msg='File not found'), 404

@posts_bp.route('/edit-post/<int:post_id>', methods=['PUT'])
@jwt_required()
def edit_post(post_id):
    current_post = Post.query.filter_by(id=post_id, creator_id=current_user.id).one_or_none()
    if not current_post: return jsonify(msg='Post not found'), 404

    data = request.get_json()
    if not data:
        return jsonify(msg="No data provided"), 400

    fields = ('title', 'price', 'description')
    errors = {}
    for k in fields:
        if k in data:
            value = data[k]
            if k == 'title':
                if not isinstance(value, str) or len(value.strip()) < 5:
                    errors[k] = 'Title must be at least 5 characters long'
            elif k == 'price':
                try:
                    value = float(value)
                    if value < 0:
                        errors[k] = 'Price must be positive'
                except (ValueError, TypeError):
                    errors[k] = 'Price must be a number'
            elif k == 'description':
                if not isinstance(value, str) or len(value.strip()) < 10:
                    errors[k] = 'description must be at least 10 characters long'

            setattr(current_post, k, value)

    if errors:
        return jsonify(errors=errors), 400

    db.session.commit()
    return jsonify(msg="Post updated successfully", post_id=current_post.id)

@posts_bp.route('/delete/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id, creator_id=current_user.id).one_or_none()
    if not post:
        return jsonify(msg='Post not found'), 404

    response = dict()
    if os.path.isdir(post.img_path):
        try:
            shutil.rmtree(post.img_path)
            response.update({'removed_directory': post.img_path})
        except Exception as e:
            print(f'Error while deleting post {post.id}: {e}')

    db.session.delete(post)
    db.session.commit()
    response.update({'deleted_post_id': post.id})

    return jsonify(**response), 200






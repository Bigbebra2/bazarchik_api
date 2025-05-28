from .extensions import db
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    reg_datetime = db.Column(db.DateTime, default=lambda : datetime.now(timezone.utc))
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete')
    posts = db.relationship('Post', backref='creator', uselist=True, cascade='all, delete')


class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    age = db.Column(db.Integer)
    bio = db.Column(db.String(500))
    phone_number = db.Column(db.String(14))
    location = db.Column(db.String(100))
    img_path = db.Column(db.String(255))


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(1500))
    img_path = db.Column(db.String(255))
    creation_date = db.Column(db.DateTime, default=lambda : datetime.now(timezone.utc))


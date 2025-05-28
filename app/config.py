from dotenv import load_dotenv
from os import getenv, getcwd, path


load_dotenv()

class Config:
    SECRET_KEY = getenv('SECRET_KEY', 'default-secret')
    JWT_SECRET_KEY = getenv('JWT_SECRET_KEY', 'default-secret-jwt')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_SUPPORTS_CREDENTIALS = True
    UPLOAD_FOLDER = path.join(getcwd(), 'uploads')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]



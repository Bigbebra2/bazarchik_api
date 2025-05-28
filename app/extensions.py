from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import redis


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
redis_blocklist = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from redis import Redis
import pymysql


pymysql.install_as_MySQLdb()
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
redis_blocklist = Redis.from_url(
    "redis://default:cOqJtKeaNnKkxiQctqXYUboJeIXXOixF@yamanote.proxy.rlwy.net:22695",
    decode_responses=True
)

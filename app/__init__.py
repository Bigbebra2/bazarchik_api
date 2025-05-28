from flask import Flask
from .config import Config
from .extensions import db, jwt, cors, migrate
from .routes import register_routes
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "https://bazarchik-five.vercel.app",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5000",
                "http://127.0.0.1:5000"
            ]
        }
    })

    upload_folder = os.path.join(os.getcwd(), "uploads", "avas")
    os.makedirs(upload_folder, exist_ok=True)

    register_routes(app)

    return app


from . import models
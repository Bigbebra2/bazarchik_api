from .posts import posts_bp
from .auth import auth_bp
from .profile import profile_bp


def register_routes(app):
    app.register_blueprint(posts_bp, url_prefix='/api/posts')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')

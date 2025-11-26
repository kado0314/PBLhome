from flask import Flask
from .routes import scoring_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(scoring_bp)
    return app

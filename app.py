from flask import Flask
from flask_cors import CORS

from config import SECRET_KEY, SESSION_CONFIG
from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp
from routes.persona import persona_bp
from routes.reportes import reportes_bp
from routes.finex_app import finex_bp
from oauth_config import init_oauth

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    for key, value in SESSION_CONFIG.items():
        app.config[key] = value

    CORS(app, supports_credentials=True)
    init_oauth(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(persona_bp, url_prefix="/dashboard")
    app.register_blueprint(reportes_bp)
    app.register_blueprint(finex_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

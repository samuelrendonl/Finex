from flask import Flask
from flask_cors import CORS
from config import SECRET_KEY, SESSION_CONFIG

from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp

from oauth_config import init_oauth

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Config sesión
for key, value in SESSION_CONFIG.items():
    app.config[key] = value
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
# CORS
CORS(app, supports_credentials=True)

# OAuth

init_oauth(app)

# Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)

if __name__ == "__main__":
    app.run(debug=True)
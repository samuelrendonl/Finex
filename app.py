from flask import Flask
from flask_cors import CORS

from config import SECRET_KEY, SESSION_CONFIG

from routes.main import main_bp
from routes.auth import auth_bp
from routes.user import user_bp
from routes.persona import persona_bp
from routes.reportes import reportes_bp

from oauth_config import init_oauth

app = Flask(__name__)
app.secret_key = SECRET_KEY

# SESSION
for key, value in SESSION_CONFIG.items():
    app.config[key] = value

# CORS
CORS(app, supports_credentials=True)

# OAUTH
init_oauth(app)

# BLUEPRINTS
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)

app.register_blueprint(persona_bp, url_prefix="/dashboard")
app.register_blueprint(reportes_bp)

if __name__ == "__main__":
    app.run(debug=True)
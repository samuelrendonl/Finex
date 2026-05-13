from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

load_dotenv()

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    microsoft_tenant = os.getenv("MICROSOFT_TENANT", "common")
    if microsoft_client_id and microsoft_client_secret:
        oauth.register(
            name="microsoft",
            client_id=microsoft_client_id,
            client_secret=microsoft_client_secret,
            server_metadata_url=f"https://login.microsoftonline.com/{microsoft_tenant}/v2.0/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

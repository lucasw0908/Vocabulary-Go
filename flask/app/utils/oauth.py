import logging
import os

from flask import request
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import GoogleAuthError
from google.oauth2 import id_token
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

from zenora import APIClient, APIError, OwnUser

from ..config import (
    REDIRECT_URI, 
    DISCORD_CLIENT_SECRET, DISCORD_TOKEN,
    GOOGLE_CLIENT_ID, GOOGLE_SCOPES, GOOGLE_CONFIG
)

log = logging.getLogger(__name__)

google_flow = Flow.from_client_config(
    GOOGLE_CONFIG,
    scopes=GOOGLE_SCOPES,
    redirect_uri=REDIRECT_URI
)

discord_client = APIClient(
    DISCORD_TOKEN, 
    client_secret=DISCORD_CLIENT_SECRET, 
    validate_token=False
)

class FlaskOAuth:
    
    class OAuthError(Exception): ...
    class GoogleOAuthError(OAuthError): ...
    class DiscordOAuthError(OAuthError): ...
    
    @staticmethod
    def discord() -> tuple[OwnUser, str]:
        """
        Handle Discord OAuth2 callback and return the current user and access token.
        """
        if "code" not in request.args:
            log.warning("No code provided in request arguments")
            return None
        
        code = request.args["code"]
        
        try: 
            access_token = discord_client.oauth.get_access_token(code, REDIRECT_URI).access_token
            
        except APIError as e: 
            log.warning(f"Failed to get access token: {e}")
            raise FlaskOAuth.DiscordOAuthError("Failed to get access token") from e
        
        bearer_client = APIClient(access_token, bearer=True)
        current_user = bearer_client.users.get_current_user()
        
        return current_user, access_token
        
    
    @staticmethod
    def google() -> tuple[dict, str]:
        """
        Handle Google OAuth2 callback and return the ID info and access token.  
        """
        if not REDIRECT_URI.startswith("https"):
            log.warning("Insecure transport for OAuth2, only for development use.")
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        
        try:
            google_flow.fetch_token(authorization_response=request.url)
            credentials = google_flow.credentials
            
        except OAuth2Error as e:
            log.warning(f"Failed to fetch token: {e}")
            raise FlaskOAuth.GoogleOAuthError("Failed to fetch token") from e
        
        try:
            idinfo = id_token.verify_oauth2_token(
                credentials._id_token,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )
            
        except (GoogleAuthError, ValueError) as e:
            log.warning(f"Failed to verify ID token: {e}")
            raise FlaskOAuth.GoogleOAuthError("Failed to verify ID token") from e
        
        if idinfo is None:
            log.warning("ID info is None")
            raise FlaskOAuth.GoogleOAuthError("ID info is None")
        
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            log.warning(f"Wrong issuer: {idinfo['iss']}")
            raise FlaskOAuth.GoogleOAuthError("Wrong issuer")
        
        return idinfo, credentials.token

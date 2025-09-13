import os
import subprocess
from dotenv import load_dotenv

from app import create_app
from app.config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE,
    ALWAYS_UPDATE_DIST
)


dotenv_path = os.path.join(os.path.dirname(__file__), '.flaskenv')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)
    
app = create_app()

if __name__ == "__main__":
        
    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), "app", "static", "assets", "js", "dist")) or ALWAYS_UPDATE_DIST:
        subprocess.run(
            "npm run build",
            check=True,
            cwd=os.path.join(os.path.abspath(os.path.dirname(__file__)), "app"),
            shell=True
        )
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE, use_reloader=False)
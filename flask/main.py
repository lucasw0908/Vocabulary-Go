import os
import subprocess
from dotenv import load_dotenv

from app import create_app, db
from app.config import (
    SERVER_HOST, SERVER_PORT, DEBUG_MODE,
    ALWAYS_UPDATE_DIST
)


dotenv_path = os.path.join(os.path.dirname(__file__), ".flaskenv")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)


app = create_app()


@app.shell_context_processor
def make_shell_context():
    from app.models import Users, Words, Sentences, Libraries
    return {
        "db": db, 
        "Users": Users, 
        "Words": Words, 
        "Sentences": Sentences, 
        "Libraries": Libraries
    }
    

@app.cli.command("deploy")
def deploy():
    from flask_migrate import migrate, upgrade
    migrate()
    upgrade()
    app.logger.info("Database migrated successfully.")


@app.cli.command("test")
def test():
    import pytest
    pytest.main(["-v", "tests/"])
    

if __name__ == "__main__":

    if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), "app", "static", "assets", "js", "dist")) or ALWAYS_UPDATE_DIST:
        subprocess.run(
            "npm run build",
            check=True,
            cwd=os.path.join(os.path.abspath(os.path.dirname(__file__)), "app"),
            shell=True
        )
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE, use_reloader=False)
import json
import logging
import os

from sqlalchemy.engine import Inspector

from ..config import (
    BASEDIR,
    SYSTEM_USERNAME, SYSTEM_EMAIL, SYSTEM_PASSWORD
)
from ..models import db, Libraries, Users, Words
from .checker import library_checker


log = logging.getLogger(__name__)


def init_system_user() -> None:
    """
    Initialize the system user with default credentials.
    This method should be called once during application startup.
    """
    
    if len(Users.query.all()) > 0:
        return
    
    db.session.add(Users(
        username=SYSTEM_USERNAME,
        password=SYSTEM_PASSWORD,
        email=SYSTEM_EMAIL
    ))
    db.session.commit()
    
    log.info(f"System user initialized with username '{SYSTEM_USERNAME}' and email '{SYSTEM_EMAIL}'.")
    
    
def load_libraries() -> None:
    """
    Load the libraries from the database.
    This method should be called once during application startup.
    """
    
    library_path = os.path.join(BASEDIR, "library")
    library_files = [file for file in os.listdir(library_path) if file.endswith(".json")]
        
    for library_file in library_files:
        
        # Load files
        with open(os.path.join(library_path, library_file), "r", encoding="utf-8") as f:
            
            try: 
                library_json: dict[str, str | list[dict[str, str]]] = json.load(f)
                library_checker(library_json)
                
            except json.JSONDecodeError:
                log.warning(f"Invalid JSON format in {library_file}. Skipping this library.")
                continue
            
            except Exception as e:
                log.warning(f"Error validating {library_file}: {e}. Skipping this library.")
                continue
            
            keys = ["name", "description", "created_at", "updated_at", "author", "words"]
            
            if set(library_json.keys()) != set(keys):
                log.warning(f"Invalid keys in {library_file}. Expected keys: {keys}. Skipping this library.")
                continue
            
        # Database
        if Libraries.query.filter_by(name=library_json["name"]).first():
            log.error(f"Library {library_json['name']} already exists in the database. Skipping this library.")
            continue
        
        author_id = author.id if (author := Users.query.filter_by(username=library_json["author"]).first()) else None

        db.session.add(library := (Libraries(
            name=library_json["name"],
            description=library_json["description"],
            public=True,
            author_id=author_id or 1 # Default to system user if author not found
        )))
        db.session.commit()
        
        log.debug(f"Added library {library.name} to the database. ID: {library.id}")
        
        for word in library_json["words"]:
            
            chinese = word.get("Chinese")
            english = word.get("English")
            
            if (not chinese) or (not english):
                log.warning(f"Missing 'Chinese' or 'English' in word {word}. Skipping this word.")
                continue
            
            word_instance = Words(
                chinese=chinese,
                english=english
            )
            word_instance._library_id = library.id
            
            db.session.add(word_instance)
            

        db.session.commit()

    log.info("Libraries loaded from the library directory.")
    
    
def init_models() -> None:
    """
    Initialize the database models.
    This method should be called once during application startup.
    """
    
    db.create_all()
    inspector = Inspector.from_engine(db.engine)
    tables = inspector.get_table_names()

    log.info(f"Database models initialized. Tables: {tables}")
    
    init_system_user()
    load_libraries()
    
    log.info("All models initialized successfully.")
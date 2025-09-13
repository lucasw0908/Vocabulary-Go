import logging
import re
import os
from typing import Any

from PIL import Image

from ..config import BASEDIR, DEFAULT_AVATAR_FOLDER


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
FILE_RE = re.compile(r'^(?!\.)(?!.*[ .]$)(?!.*[<>:"/\\|?*\x00-\x1F])(?!(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$)[^/\\\x00-\x1F]{1,255}$')

log = logging.getLogger(__name__)


def allowed_file(filename: str) -> bool:    
    
    if not isinstance(filename, str):
        log.warning(f"Filename '{filename}' is not a string.")
        return False
    
    if not FILE_RE.fullmatch(filename):
        log.warning(f"Filename '{filename}' does not match the allowed pattern.")
        return False
    
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(image: Any, filename: str) -> None:
    
    log.debug(f"Processing image with filename: {filename}")
    
    if not allowed_file(filename):
        log.error(f"Invalid filename '{filename}' for image processing.")
        raise ValueError("Invalid filename for image processing")
    
    path = os.path.join(BASEDIR, "static", DEFAULT_AVATAR_FOLDER)
    
    if not os.path.exists(path):
        os.makedirs(path)
        log.debug(f"Created directory for avatars at {path}.")

    try:
        image: Image.Image = Image.open(image)
        image.thumbnail((128, 128))
        image.save(os.path.join(path, filename), format="PNG", optimize=True)
        log.debug(f"Image saved successfully at {os.path.join(path, filename)}.")
    
    except Exception as e:
        log.error(f"Error processing image: {e}")
        raise ValueError("Invalid image file")
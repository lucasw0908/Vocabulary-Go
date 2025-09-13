import io
import requests
import os

from app.config import BASEDIR, DEFAULT_AVATAR_FOLDER
from app.utils.image_processing import process_image


def test_process_image():
    path = os.path.join(BASEDIR, "static", DEFAULT_AVATAR_FOLDER, "test_image.png")
    resp = requests.get("https://cdn.discordapp.com/emojis/1295717257145618513.webp?size=96", stream=True)
    img_file = io.BytesIO(resp.content)
    
    try:
        process_image(img_file, "test_image.png")
        assert os.path.exists(path)
        
    except ValueError as e:
        assert False, f"Image processing failed: {e}"
    
    if os.path.exists(path):
        os.remove(path)
# config.py

import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # Load from environment variable or use default
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')  # Load from environment variable or use default
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size for uploads

def create_upload_folders():
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)

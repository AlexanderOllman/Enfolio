import os
from datetime import timedelta

class Config:
    # ... existing config ...
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CSRF Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = timedelta(hours=1)
    WTF_CSRF_SSL_STRICT = True
    
    # Make sure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
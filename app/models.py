from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from app import db
from slugify import slugify
import uuid

class Content(db.Model):
    id = db.Column(db.String(250), primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # For Experience type
    company = db.Column(db.String(200))
    position = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # For Project type
    github_url = db.Column(db.String(500))
    live_url = db.Column(db.String(500))
    technologies = db.Column(db.String(500))
    
    # Page Builder content - available for all content types
    page_content = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def generate_id(self):
        """Generate a unique ID based on the title"""
        if not self.title:
            return str(uuid.uuid4())
            
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        
        # Keep checking until we find a unique slug
        while Content.query.get(slug) is not None:
            slug = f"{base_slug}-{counter}"
            counter += 1
            
            # Failsafe: if we somehow can't find a unique slug, use UUID
            if counter > 100:
                slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
                break
        
        return slug

    def __init__(self, *args, **kwargs):
        # Set a temporary UUID as ID
        kwargs['id'] = str(uuid.uuid4())
        super(Content, self).__init__(*args, **kwargs)
        
        # After initialization, if we have a title, generate the proper ID
        if self.title:
            self.id = self.generate_id()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    github_url = db.Column(db.String(500))
    attachment_url = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to link to Content
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # Store the type of content it's linked to
    
    # Relationship
    related_content = db.relationship('Content', backref=db.backref('journal_entries', lazy=True))
from app import create_app, db
from app.models import User, Content

app = create_app()

def init_db():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Available tables:", tables)
        
        # Create a test user
        user = User(username='admin')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        print('Database initialized and test user created!')
        print('Username: admin')
        print('Password: password123')

if __name__ == '__main__':
    init_db() 
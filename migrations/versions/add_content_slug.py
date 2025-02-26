"""Convert id to slug-based string

Revision ID: add_content_slug
Revises: 751b80dc5260
Create Date: 2024-01-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from slugify import slugify

# revision identifiers, used by Alembic.
revision = 'add_content_slug'
down_revision = '751b80dc5260'
branch_labels = None
depends_on = None

def upgrade():
    # Create new table with string ID
    op.create_table(
        'content_new',
        sa.Column('id', sa.String(250), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('content', sa.Text),
        sa.Column('image_url', sa.String(500)),
        sa.Column('date_created', sa.DateTime),
        sa.Column('date_modified', sa.DateTime),
        sa.Column('company', sa.String(200)),
        sa.Column('position', sa.String(200)),
        sa.Column('start_date', sa.Date),
        sa.Column('end_date', sa.Date),
        sa.Column('github_url', sa.String(500)),
        sa.Column('live_url', sa.String(500)),
        sa.Column('technologies', sa.String(500)),
        sa.Column('page_content', sa.JSON),
        sa.Column('created_at', sa.DateTime),
        sa.Column('modified_at', sa.DateTime)
    )
    
    # Copy data from old table to new table with slug IDs
    connection = op.get_bind()
    content_items = connection.execute(sa.text('SELECT * FROM content')).fetchall()
    
    for content in content_items:
        # Generate slug from title
        base_slug = slugify(content.title)
        new_id = base_slug
        counter = 1
        
        # Check for duplicate slugs
        while connection.execute(
            sa.text('SELECT id FROM content_new WHERE id = :new_id'),
            {'new_id': new_id}
        ).fetchone() is not None:
            new_id = f"{base_slug}-{counter}"
            counter += 1
        
        # Insert into new table
        connection.execute(
            sa.text('''
                INSERT INTO content_new 
                (id, type, title, description, content, image_url, 
                date_created, date_modified, company, position, 
                start_date, end_date, github_url, live_url, 
                technologies, page_content, created_at, modified_at)
                VALUES 
                (:id, :type, :title, :description, :content, :image_url,
                :date_created, :date_modified, :company, :position,
                :start_date, :end_date, :github_url, :live_url,
                :technologies, :page_content, :created_at, :modified_at)
            '''),
            {
                'id': new_id,
                'type': content.type,
                'title': content.title,
                'description': content.description,
                'content': content.content,
                'image_url': content.image_url,
                'date_created': content.date_created,
                'date_modified': content.date_modified,
                'company': content.company,
                'position': content.position,
                'start_date': content.start_date,
                'end_date': content.end_date,
                'github_url': content.github_url,
                'live_url': content.live_url,
                'technologies': content.technologies,
                'page_content': content.page_content,
                'created_at': content.created_at,
                'modified_at': content.modified_at
            }
        )
    
    # Drop old table and rename new table
    op.drop_table('content')
    op.rename_table('content_new', 'content')

def downgrade():
    # Create new table with integer ID
    op.create_table(
        'content_new',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('content', sa.Text),
        sa.Column('image_url', sa.String(500)),
        sa.Column('date_created', sa.DateTime),
        sa.Column('date_modified', sa.DateTime),
        sa.Column('company', sa.String(200)),
        sa.Column('position', sa.String(200)),
        sa.Column('start_date', sa.Date),
        sa.Column('end_date', sa.Date),
        sa.Column('github_url', sa.String(500)),
        sa.Column('live_url', sa.String(500)),
        sa.Column('technologies', sa.String(500)),
        sa.Column('page_content', sa.JSON),
        sa.Column('created_at', sa.DateTime),
        sa.Column('modified_at', sa.DateTime)
    )
    
    # Copy data from old table to new table with integer IDs
    connection = op.get_bind()
    content_items = connection.execute(sa.text('SELECT * FROM content ORDER BY date_created')).fetchall()
    
    for idx, content in enumerate(content_items, 1):
        connection.execute(
            sa.text('''
                INSERT INTO content_new 
                (id, type, title, description, content, image_url, 
                date_created, date_modified, company, position, 
                start_date, end_date, github_url, live_url, 
                technologies, page_content, created_at, modified_at)
                VALUES 
                (:id, :type, :title, :description, :content, :image_url,
                :date_created, :date_modified, :company, :position,
                :start_date, :end_date, :github_url, :live_url,
                :technologies, :page_content, :created_at, :modified_at)
            '''),
            {
                'id': idx,
                'type': content.type,
                'title': content.title,
                'description': content.description,
                'content': content.content,
                'image_url': content.image_url,
                'date_created': content.date_created,
                'date_modified': content.date_modified,
                'company': content.company,
                'position': content.position,
                'start_date': content.start_date,
                'end_date': content.end_date,
                'github_url': content.github_url,
                'live_url': content.live_url,
                'technologies': content.technologies,
                'page_content': content.page_content,
                'created_at': content.created_at,
                'modified_at': content.modified_at
            }
        )
    
    # Drop old table and rename new table
    op.drop_table('content')
    op.rename_table('content_new', 'content') 
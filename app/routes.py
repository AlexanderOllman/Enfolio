from flask import render_template, Blueprint, request, redirect, url_for, flash, abort, jsonify, session
from flask_login import login_required, current_user
from app.models import Content, Journal
from app import db
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import time
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from app.utils.image_utils import ImageGenerator
from app.utils.company_utils import CompanySearch

main = Blueprint('main', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize CSRF protection
csrf = CSRFProtect()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    # Fetch only live content items, ordered by date
    content_items = Content.query.filter_by(is_live=True).order_by(Content.date_created.desc()).all()
    
    # Pass content_items to the template
    return render_template('index.html', content_items=content_items)

@main.route('/admin')
@login_required
def admin():
    return redirect(url_for('main.admin_home'))

@main.route('/admin/home')
@login_required
def admin_home():
    # Get all content and sort by date
    all_content = Content.query.order_by(Content.date_created.desc()).all()
    recent_content = all_content[:5] if all_content else []
    
    # Get counts for metrics cards
    projects_count = Content.query.filter_by(type='project').count()
    blog_count = Content.query.filter_by(type='blog').count()
    experience_count = Content.query.filter_by(type='experience').count()
    
    # Get all journal entries
    all_journal_entries = Journal.query.all()
    
    # Get 5 most recent journal entries for display
    recent_journal_entries = Journal.query.order_by(Journal.date_created.desc()).limit(5).all()
    
    # Get profile image if it exists (or use a default)
    user_image = 'default-profile.jpg'  # Default image
    # In the future, we could load the actual user's profile image
    
    # Define upcoming tasks - would come from a tasks table in a real implementation
    upcoming_tasks = [
        {
            'name': 'Complete Portfolio Profile',
            'date': 'Sep 13, 08:30',
            'icon': 'chat',
            'completed': True
        },
        {
            'name': 'Setup Basic Portfolio',
            'date': 'Sep 13, 10:30',
            'icon': 'people',
            'completed': True
        },
        {
            'name': 'Add First Project',
            'date': 'Sep 13, 13:00',
            'icon': 'file-text',
            'completed': False
        },
        {
            'name': 'Write Bio',
            'date': 'Sep 13, 14:45',
            'icon': 'pen',
            'completed': False
        },
        {
            'name': 'Configure SEO Settings',
            'date': 'Sep 13, 16:30',
            'icon': 'gear',
            'completed': False
        }
    ]
    
    # Define calendar events - would come from an events table in a real implementation
    calendar_events = [
        {
            'title': 'Weekly Content Update',
            'day': 24,
            'type': 'work',
            'attendees': 3
        },
        {
            'title': 'Portfolio Review',
            'day': 28,
            'type': 'personal',
            'attendees': 2
        }
    ]
    
    # Calculate progress percentages
    content_completion = 75  # Example percentages
    design_completion = 40
    seo_completion = 60
    overall_completion = 55
    
    # Calculate onboarding progress
    completed_tasks = sum(1 for task in upcoming_tasks if task['completed'])
    total_tasks = len(upcoming_tasks)
    onboarding_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    return render_template('admin/home.html', 
                         content=all_content, 
                         recent_content=recent_content,
                         journal_entries=all_journal_entries,
                         recent_journal_entries=recent_journal_entries,
                         projects_count=projects_count,
                         blog_count=blog_count,
                         experience_count=experience_count,
                         user_image=user_image,
                         upcoming_tasks=upcoming_tasks,
                         calendar_events=calendar_events,
                         content_completion=content_completion,
                         design_completion=design_completion,
                         seo_completion=seo_completion,
                         overall_completion=overall_completion,
                         onboarding_percentage=onboarding_percentage,
                         completed_tasks=completed_tasks,
                         total_tasks=total_tasks)

@main.route('/admin/projects')
@login_required
def admin_projects():
    projects = Content.query.filter_by(type='project').all()
    return render_template('admin/projects.html', projects=projects)

@main.route('/admin/experience')
@login_required
def admin_experience():
    experiences = Content.query.filter_by(type='experience').all()
    return render_template('admin/experience.html', experiences=experiences)

@main.route('/admin/blog')
@login_required
def admin_blog():
    posts = Content.query.filter_by(type='blog').all()
    return render_template('admin/blog.html', posts=posts)

@main.route('/admin/journal')
@login_required
def admin_journal():
    journal_entries = Journal.query.order_by(Journal.date_created.desc()).all()
    return render_template('admin/journal.html', entries=journal_entries)

@main.route('/admin/journal/manage', defaults={'id': None}, methods=['GET', 'POST'])
@main.route('/admin/journal/manage/<string:id>', methods=['GET', 'POST'])
@login_required
def manage_journal(id):
    from werkzeug.utils import secure_filename
    form = FlaskForm()
    
    # Get all content to power the "search" for linked content
    all_content = Content.query.order_by(Content.date_created.desc()).all()
    content_list = [{
        'id': content.id,
        'type': content.type,
        'title': content.title,
    } for content in all_content]
    
    if id:
        # EDIT MODE
        journal = Journal.query.get_or_404(id)
        if request.method == 'POST' and form.validate_on_submit():
            journal.content = request.form.get('content')
            journal.github_url = request.form.get('github_url')
            journal.content_id = request.form.get('content_id')
            
            # Update the images field from the carousel (a JSON string)
            journal.images = request.form.get('images')
            
            # Update the journal date if provided
            journal_date = request.form.get('journal_date')
            if journal_date:
                try:
                    journal.date_created = datetime.strptime(journal_date, '%Y-%m-%d')
                except ValueError:
                    pass
            
            # Handle multiple attachments upload (allowing any file type)
            attachment_files = request.files.getlist('attachment')
            if attachment_files:
                attachments_list = []
                for file in attachment_files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        attachments_list.append(filename)
                # Save attachments as a JSON string
                if attachments_list:
                    journal.attachments = json.dumps(attachments_list)
            
            db.session.commit()
            flash('Journal entry updated successfully!', 'success')
            return redirect(url_for('main.admin_journal'))
        
        # Get currently linked content for pre-populating the search field
        current_content_obj = Content.query.get(journal.content_id)
        current_content = None
        if current_content_obj:
            current_content = {
                'id': current_content_obj.id,
                'type': current_content_obj.type,
                'title': current_content_obj.title,
            }
        
        return render_template(
            'admin/journal_form.html',
            journal=journal,
            form=form,
            content=content_list,
            current_content=current_content,
            current_date=journal.date_created.strftime('%Y-%m-%d') if journal.date_created else ''
        )
    else:
        # CREATE MODE
        if request.method == 'POST' and form.validate_on_submit():
            content_id = request.form.get('content_id')
            linked_content = Content.query.get_or_404(content_id)
            
            new_journal = Journal(
                content_id=content_id,
                content_type=linked_content.type,
                content=request.form.get('content'),
                github_url=request.form.get('github_url'),
                images=request.form.get('images')  # Images field from carousel
            )
            
            journal_date = request.form.get('journal_date')
            if journal_date:
                try:
                    new_journal.date_created = datetime.strptime(journal_date, '%Y-%m-%d')
                except ValueError:
                    pass
            
            # Handle multiple attachments upload (allowing any file type)
            attachment_files = request.files.getlist('attachment')
            if attachment_files:
                attachments_list = []
                for file in attachment_files:
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        attachments_list.append(filename)
                if attachments_list:
                    new_journal.attachments = json.dumps(attachments_list)
            
            db.session.add(new_journal)
            db.session.commit()
            flash('Journal entry created successfully!', 'success')
            return redirect(url_for('main.admin_journal'))
        
        # For new entries, use the most recent content to pre-populate if available
        last_edited = all_content[0] if all_content else None
        last_edited_dict = None
        if last_edited:
            last_edited_dict = {
                'id': last_edited.id,
                'type': last_edited.type,
                'title': last_edited.title,
            }
        
        return render_template(
            'admin/journal_form.html',
            journal=None,
            form=form,
            content=content_list,
            current_content=last_edited_dict,
            current_date=datetime.today().strftime('%Y-%m-%d')
        )

@main.route('/admin/create_new', methods=['GET', 'POST'])
@login_required
def create_new():
    form = FlaskForm()
    if request.method == 'POST' and form.validate_on_submit():
        content_type = request.form.get('type')
        
        # Create new content object
        content = Content(
            type=content_type,
            title=request.form.get('title'),
            description=request.form.get('description'),
            page_content=json.loads(request.form.get('page_content', '[]'))
        )
        
        # Handle image upload if provided
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                content.image_url = filename

        # Add type-specific fields
        if content_type == 'project':
            content.technologies = request.form.get('technologies')
            content.github_url = request.form.get('github_url')
            content.live_url = request.form.get('live_url')
        elif content_type == 'experience':
            content.company = request.form.get('company')
            content.position = request.form.get('position')
            content.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
            content.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
            
            # Add new experience fields
            content.employment_type = request.form.get('employment_type')
            content.location = request.form.get('location')
            content.is_remote = True if request.form.get('is_remote') else False
            content.team_size = request.form.get('team_size')
            content.key_achievements = request.form.get('key_achievements')
            content.skills = request.form.get('skills')
            content.responsibilities = request.form.get('responsibilities')
        elif content_type == 'blog':
            content.content = request.form.get('content')

        try:
            db.session.add(content)
            db.session.commit()
            flash(f'{content_type.title()} created successfully!', 'success')
            return redirect(url_for(f'main.admin_{content_type}s'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating content: {str(e)}', 'error')
            return render_template('admin/content_form.html', form=form, content=None)

    return render_template('admin/content_form.html', form=form, content=None)

@main.route('/admin/<string:type>/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_content_by_type(type, id):
    # Get the existing content
    content = Content.query.get_or_404(id)

    form = FlaskForm()

    if form.validate_on_submit():
        # Update common fields
        content.title = form.title.data
        content.description = form.description.data
        content.type = type
        
        # Process image upload
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            if image_filename:
                form.image.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
                content.image_url = image_filename
        
        # Process screenshots uploads
        if request.form.getlist('screenshots'):
            screenshots = request.form.getlist('screenshots')
            content.screenshots = screenshots
        
        # Process content type-specific fields
        if type == 'project':
            content.github_url = form.github_url.data
            content.live_url = form.project_url.data
            content.technologies = form.tech_stack.data
            content.project_status = form.project_status.data
            content.project_client = form.project_client.data
        elif type == 'experience':
            content.company = form.company.data
            content.position = form.position.data
            content.location = form.location.data
            content.employment_type = form.employment_type.data
            content.is_remote = form.is_remote.data
            content.start_date = form.start_date.data
            content.end_date = form.end_date.data
            content.key_achievements = form.key_achievements.data
            content.responsibilities = form.responsibilities.data
            content.skills = form.skills.data
            content.team_size = form.team_size.data
        elif type == 'blog':
            content.content = form.blog_content.data
            content.status = form.status.data
            content.tags = form.tags.data
            content.read_time = form.read_time.data
        
        # Update page content if provided
        if form.page_content.data:
            try:
                page_content = json.loads(form.page_content.data)
                content.page_content = page_content
            except Exception as e:
                flash(f'Error parsing page content: {str(e)}', 'danger')
        
        db.session.commit()
        flash(f'{type.capitalize()} updated successfully!', 'success')
        return redirect(url_for(f'main.admin_{type}s'))
    
    # Fill the form with existing data
    form.title.data = content.title
    form.description.data = content.description
    
    if type == 'project':
        form.github_url.data = content.github_url
        form.project_url.data = content.live_url
        form.tech_stack.data = content.technologies
        form.project_status.data = content.project_status
        form.project_client.data = content.project_client
    elif type == 'experience':
        form.company.data = content.company
        form.position.data = content.position
        form.location.data = content.location
        form.employment_type.data = content.employment_type
        form.is_remote.data = content.is_remote
        form.start_date.data = content.start_date
        form.end_date.data = content.end_date
        form.key_achievements.data = content.key_achievements
        form.responsibilities.data = content.responsibilities
        form.skills.data = content.skills
        form.team_size.data = content.team_size
    elif type == 'blog':
        form.blog_content.data = content.content
        form.status.data = content.status
        form.tags.data = content.tags
        form.read_time.data = content.read_time

    return render_template('admin/content_form.html', form=form, content=content)

@main.route('/content/<string:id>/delete', methods=['POST'])
@login_required
def delete_content(id):
    try:
        content = Content.query.get_or_404(id)
        content_type = content.type
        db.session.delete(content)
        db.session.commit()
        flash(f'{content_type.title()} deleted successfully!', 'success')
        return redirect(url_for(f'main.admin_{content_type}'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting: {str(e)}', 'error')
        return redirect(url_for('main.admin_home'))

@main.route('/preview/project/<string:id>')
def preview_project(id):
    project = Content.query.get_or_404(id)
    if project.type != 'project':
        abort(404)
    
    # Render the frontend project template instead of the admin details template
    return render_template('preview/project.html', project=project, title=project.title)

@main.route('/project/<string:id>')
def view_project(id):
    project = Content.query.get_or_404(id)
    if project.type != 'project':
        abort(404)
    
    # Find related projects based on technologies
    related_content = []
    if project.technologies:
        tech_list = [tech.strip() for tech in project.technologies.split(',')]
        # Find projects with similar technologies
        related_projects = Content.query.filter(
            Content.type == 'project',
            Content.id != project.id
        ).all()
        
        # Score projects by number of matching technologies
        scored_projects = []
        for related in related_projects:
            if related.technologies:
                related_techs = [t.strip() for t in related.technologies.split(',')]
                matching = len(set(tech_list) & set(related_techs))
                if matching > 0:
                    scored_projects.append((related, matching))
        
        # Sort by score and take top 3
        scored_projects.sort(key=lambda x: x[1], reverse=True)
        related_content = [p[0] for p in scored_projects[:3]]
    
    # Get CSRF token from session
    csrf_token = session.get('csrf_token', '')
    
    return render_template('details.html', content=project, related_content=related_content, csrf_token=csrf_token)

@main.route('/preview/experience/<string:id>')
def preview_experience(id):
    experience = Content.query.get_or_404(id)
    if experience.type != 'experience':
        abort(404)
    
    # Render the frontend experience template
    return render_template('preview/experience.html', experience=experience, title=experience.title)

@main.route('/experience/<string:id>')
def view_experience(id):
    experience = Content.query.get_or_404(id)
    if experience.type != 'experience':
        abort(404)
    
    # Find related experiences based on skills
    related_content = []
    if experience.skills:
        skill_list = [skill.strip() for skill in experience.skills.split(',')]
        # Find experiences with similar skills
        related_experiences = Content.query.filter(
            Content.type == 'experience',
            Content.id != experience.id
        ).all()
        
        # Score experiences by number of matching skills
        scored_experiences = []
        for related in related_experiences:
            if related.skills:
                related_skills = [s.strip() for s in related.skills.split(',')]
                matching = len(set(skill_list) & set(related_skills))
                if matching > 0:
                    scored_experiences.append((related, matching))
        
        # Sort by score and take top 3
        scored_experiences.sort(key=lambda x: x[1], reverse=True)
        related_content = [e[0] for e in scored_experiences[:3]]
    
    # Get CSRF token from session
    csrf_token = session.get('csrf_token', '')
    
    return render_template('details.html', content=experience, related_content=related_content, csrf_token=csrf_token)

@main.route('/preview/blog/<string:id>')
def preview_blog(id):
    blog = Content.query.get_or_404(id)
    if blog.type != 'blog':
        abort(404)
    
    # Render the frontend blog template
    return render_template('preview/blog.html', blog=blog, title=blog.title)

@main.route('/blog/<string:id>')
def view_blog(id):
    blog = Content.query.get_or_404(id)
    if blog.type != 'blog':
        abort(404)
    
    # Find related blog posts based on tags
    related_content = []
    if blog.tags:
        tag_list = [tag.strip() for tag in blog.tags.split(',')]
        # Find blogs with similar tags
        related_blogs = Content.query.filter(
            Content.type == 'blog',
            Content.id != blog.id
        ).all()
        
        # Score blogs by number of matching tags
        scored_blogs = []
        for related in related_blogs:
            if related.tags:
                related_tags = [t.strip() for t in related.tags.split(',')]
                matching = len(set(tag_list) & set(related_tags))
                if matching > 0:
                    scored_blogs.append((related, matching))
        
        # Sort by score and take top 3
        scored_blogs.sort(key=lambda x: x[1], reverse=True)
        related_content = [b[0] for b in scored_blogs[:3]]
    
    # Get CSRF token from session
    csrf_token = session.get('csrf_token', '')
    
    return render_template('details.html', content=blog, related_content=related_content, csrf_token=csrf_token)

@main.route('/admin/create', methods=['POST'])
def create_content():
    content_type = request.form.get('type')
    
    # Create new content object
    content = Content(
        type=content_type,
        title=request.form.get('title'),
        description=request.form.get('description'),
        page_content=json.loads(request.form.get('page_content', '[]'))
    )
    
    # Handle image upload if provided
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            content.image_url = filename
    # For company logos from URL (when company search is used)
    elif content_type == 'experience' and request.form.get('company_logo_url'):
        logo_url = request.form.get('company_logo_url')
        if logo_url.startswith('http'):
            # It's an external URL - we'll store it directly
            content.image_url = logo_url
        else:
            # It's a filename from our own uploads folder
            content.image_url = logo_url

    # Add type-specific fields
    if content_type == 'project':
        content.technologies = request.form.get('technologies')
        content.github_url = request.form.get('github_url')
        content.live_url = request.form.get('live_url')
    elif content_type == 'experience':
        content.company = request.form.get('company')
        content.position = request.form.get('position')
        content.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
        content.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
        
        # Add new experience fields
        content.employment_type = request.form.get('employment_type')
        content.location = request.form.get('location')
        content.is_remote = True if request.form.get('is_remote') else False
        content.team_size = request.form.get('team_size')
        content.key_achievements = request.form.get('key_achievements')
        content.skills = request.form.get('skills')
        content.responsibilities = request.form.get('responsibilities')
    elif content_type == 'blog':
        content.content = request.form.get('content')

    db.session.add(content)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

@main.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Add timestamp to filename to prevent duplicates
            timestamp = int(time.time())
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            
            # Ensure upload directory exists
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            # Save the file
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Return the URL for the uploaded image
            image_url = url_for('static', filename=f'uploads/{filename}')
            
            return jsonify({
                'url': image_url,
                'success': True
            })
        except Exception as e:
            print(f"Upload error: {str(e)}")  # Add logging
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@main.route('/admin/journal/<string:id>/delete', methods=['POST'])
@login_required
def delete_journal(id):
    try:
        journal = Journal.query.get_or_404(id)
        db.session.delete(journal)
        db.session.commit()
        flash('Journal entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the journal entry: ' + str(e), 'error')
    return redirect(url_for('main.admin_journal'))

@main.route('/generate-image', methods=['POST'])
@login_required
def generate_image():
    """
    Generate an image using OpenAI's DALL-E model based on title and description 
    for projects and blog posts
    """
    try:
        # Check if we have JSON data
        if not request.is_json:
            print("Request is not JSON. Content-Type:", request.headers.get('Content-Type'))
            return jsonify({
                'success': False,
                'error': 'Invalid content type. Expected application/json'
            }), 400
            
        # Check required fields in request
        data = request.json
        if not data or 'title' not in data or 'description' not in data or 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Title, description, and type are required'
            }), 400
        
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        content_type = data.get('type', 'project').lower()
        
        # Validate inputs
        if not title or not description:
            return jsonify({
                'success': False,
                'error': 'Title and description cannot be empty'
            }), 400
        
        if content_type not in ['project', 'blog']:
            return jsonify({
                'success': False,
                'error': 'Type must be either "project" or "blog"'
            }), 400
        
        try:
            # Initialize the image generator
            generator = ImageGenerator()
            
            # Generate the image
            filename = generator.generate_content_image(
                title, 
                description, 
                type_content=content_type,
                upload_folder=UPLOAD_FOLDER
            )
            
            # Get the URL for the image
            image_url = url_for('static', filename=f'uploads/{filename}')
            
            return jsonify({
                'success': True,
                'filename': filename,
                'url': image_url
            })
        
        except Exception as e:
            # Log the error
            print(f"Image generation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    except Exception as e:
        print(f"Unexpected error in generate_image route: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An unexpected error occurred: {str(e)}"
        }), 500

@main.route('/search-companies', methods=['GET'])
@login_required
def search_companies():
    """Search for companies based on query string"""
    query = request.args.get('q', '')
    if not query or len(query.strip()) < 2:
        return jsonify([])
    
    try:
        company_search = CompanySearch()
        results = company_search.search_companies(query)
        return jsonify(results)
    except Exception as e:
        print(f"Company search error: {str(e)}")
        return jsonify([])

@main.route('/get-company-logo', methods=['GET'])
@login_required
def get_company_logo():
    """Get logo for a company based on domain"""
    domain = request.args.get('domain', '')
    company_name = request.args.get('name', '')
    
    if not domain or not company_name:
        return jsonify({
            'success': False,
            'error': 'Domain and company name are required'
        }), 400
    
    try:
        company_search = CompanySearch()
        logo_filename = company_search.get_company_logo(domain, company_name)
        
        if not logo_filename:
            return jsonify({
                'success': False,
                'error': 'Could not retrieve logo'
            }), 404
        
        # Check if the result is a URL or a local filename
        if logo_filename.startswith('http'):
            # For external fallback URLs
            return jsonify({
                'success': True,
                'is_external': True,
                'url': logo_filename
            })
        else:
            # For locally saved logos
            logo_url = url_for('static', filename=f'uploads/logos/{logo_filename}')
            return jsonify({
                'success': True,
                'is_external': False,
                'filename': logo_filename,
                'url': logo_url
            })
    
    except Exception as e:
        print(f"Logo retrieval error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/card-examples')
def card_examples():
    """Display the card examples page with the new styling."""
    return render_template('card_examples.html')

@main.route('/api/content/toggle-live', methods=['POST'])
@login_required
@csrf.exempt  # Exempt this route from CSRF protection
def toggle_content_live():
    """API endpoint to toggle the 'is_live' status of a content item"""
    try:
        data = request.get_json()
        if not data or 'id' not in data or 'is_live' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        content_id = data.get('id')
        is_live = data.get('is_live')
        
        # Find the content
        content = Content.query.get_or_404(content_id)
        
        # Update the is_live status
        content.is_live = bool(is_live)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_live': content.is_live
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
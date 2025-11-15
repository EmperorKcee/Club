import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, FileField, DateField, DecimalField
from wtforms.validators import DataRequired, Email, Optional
from datetime import datetime
from extensions import db
from models import Staff
import uuid

# Form for adding/editing staff
class StaffForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('', 'Select a role'),
        ('Manager', 'Manager'),
        ('Assistant Manager', 'Assistant Manager'),
        ('Coach', 'Coach'),
        ('Goalkeeping Coach', 'Goalkeeping Coach'),
        ('Fitness Coach', 'Fitness Coach'),
        ('Physiotherapist', 'Physiotherapist'),
        ('Doctor', 'Doctor'),
        ('Kit Manager', 'Kit Manager'),
        ('Analyst', 'Analyst'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    hire_date = DateField('Hire Date', format='%Y-%m-%d', validators=[Optional()])
    salary = DecimalField('Salary', places=2, validators=[Optional()])
    bio = TextAreaField('Bio/Notes', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    photo = FileField('Profile Picture')
    remove_photo = BooleanField('Remove current photo')

# Configure upload folder for staff photos
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'staff')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create a Blueprint for staff routes
staff_bp = Blueprint('staff', __name__, template_folder='templates')

def save_staff_photo(file):
    if not file or file.filename == '':
        return None
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'staff')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(upload_dir, unique_filename)
    
    try:
        file.save(filepath)
        return os.path.join('uploads', 'staff', unique_filename)
    except Exception as e:
        current_app.logger.error(f"Error saving staff photo: {str(e)}")
        return None

# Staff Management Routes
@staff_bp.route('/staff')
@login_required
def staff_list():
    staff_members = Staff.query.order_by(Staff.last_name, Staff.first_name).all()
    return render_template('staff/list.html', staff_members=staff_members)

@staff_bp.route('/staff/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    form = StaffForm()
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            photo_url = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename != '' and allowed_file(file.filename):
                    photo_url = save_staff_photo(file)
            
            staff = Staff(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data,
                email=form.email.data,
                phone=form.phone.data,
                hire_date=form.hire_date.data,
                photo_url=photo_url,
                bio=form.bio.data,
                salary=float(form.salary.data) if form.salary.data else None,
                is_active=form.is_active.data
            )
            
            db.session.add(staff)
            db.session.commit()
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('staff.staff_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding staff: {str(e)}")
            flash(f'Error adding staff member: {str(e)}', 'danger')
    
    return render_template('staff/form.html', form=form, staff=None)

@staff_bp.route('/staff/<int:staff_id>')
@login_required
def view_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    return render_template('staff/view.html', staff=staff)

@staff_bp.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = StaffForm(obj=staff)
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Delete old photo if exists
                    if staff.photo_url:
                        try:
                            old_photo_path = os.path.join(current_app.static_folder, staff.photo_url)
                            if os.path.exists(old_photo_path):
                                os.remove(old_photo_path)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old photo: {str(e)}")
                    
                    # Save new photo
                    staff.photo_url = save_staff_photo(file)
            
            # Handle photo removal if checkbox is checked
            if form.remove_photo.data and staff.photo_url:
                try:
                    old_photo_path = os.path.join(current_app.static_folder, staff.photo_url)
                    if os.path.exists(old_photo_path):
                        os.remove(old_photo_path)
                    staff.photo_url = None
                except Exception as e:
                    current_app.logger.error(f"Error removing photo: {str(e)}")
            
            # Update other fields
            form.populate_obj(staff)
            db.session.commit()
            
            flash('Staff member updated successfully!', 'success')
            return redirect(url_for('staff.view_staff', staff_id=staff.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating staff: {str(e)}")
            flash(f'Error updating staff member: {str(e)}', 'danger')
    
    return render_template('staff/form.html', form=form, staff=staff)

@staff_bp.route('/staff/delete/<int:staff_id>', methods=['POST'])
@login_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    
    try:
        # Delete photo if exists
        if staff.photo_url:
            try:
                photo_path = os.path.join(current_app.static_folder, staff.photo_url)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting staff photo: {str(e)}")
        
        db.session.delete(staff)
        db.session.commit()
        flash('Staff member deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting staff member: {str(e)}', 'danger')
    
    return redirect(url_for('staff.staff_list'))

import os
import uuid
from datetime import date
from werkzeug.utils import secure_filename
from flask import current_app
from pycountry import countries

def calculate_age(born):
    """
    Calculate age from date of birth.
    Returns the age as an integer.
    """
    if not born:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def get_country_code(country_name):
    """
    Convert a country name to its ISO 3166-1 alpha-2 country code.
    Returns 'zm' (Zambia) if the country is not found.
    """
    try:
        country = countries.lookup(country_name)
        return country.alpha_2.lower()
    except LookupError:
        return 'zm'  # Default to Zambia if country not found

def save_profile_picture(file, user_id):
    """
    Save uploaded profile picture and return the relative path.
    
    Args:
        file: The uploaded file object
        user_id: The ID of the user
        
    Returns:
        str: Relative path to the saved file or None if no file was provided
    """
    if not file or file.filename == '':
        return None
        
    # Create upload folder if it doesn't exist
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'profile_pictures')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate a unique filename
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    filename = secure_filename(filename)
    
    # Save the file
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Return relative path from static folder
    return os.path.join('uploads', 'profile_pictures', filename)

def delete_old_profile_picture(profile_picture):
    """
    Delete old profile picture if it exists and is not the default one.
    """
    if not profile_picture or profile_picture == 'img/default-avatar.png':
        return
        
    old_file = os.path.join(current_app.static_folder, profile_picture)
    try:
        if os.path.exists(old_file):
            os.remove(old_file)
    except Exception as e:
        current_app.logger.error(f"Error deleting old profile picture: {e}")

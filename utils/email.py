import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import render_template, current_app
from threading import Thread
from extensions import mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")

def send_email(subject, recipients, template, **kwargs):
    """Send an email using a template."""
    if not isinstance(recipients, list):
        recipients = [recipients]
    
    # Get team settings for email branding
    from models import TeamSettings
    team_settings = TeamSettings.get_settings()
    
    # Add current datetime to template context
    from datetime import datetime
    context = {
        'team_settings': team_settings,
        'now': datetime.utcnow(),
        **kwargs
    }
    
    # Render email templates
    html_body = render_template(f'emails/{template}.html', **context)
    text_body = render_template(f'emails/{template}.txt', **context)
    
    # Ensure we have valid sender information
    from_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    if not from_email:
        from_email = 'noreply@example.com'  # Fallback email
        current_app.logger.warning('MAIL_DEFAULT_SENDER not set in config, using fallback email')
    
    # Get team name or use a fallback
    team_name = getattr(team_settings, 'team_name', 'FCMS Team')
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr((team_name, from_email))
    msg['To'] = ', '.join(recipients)
    
    # Attach parts
    part1 = MIMEText(text_body, 'plain')
    part2 = MIMEText(html_body, 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email in background
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_player_credentials(player_user, password=None):
    """Send login credentials to a player."""
    subject = "Your Player Account Credentials"
    
    send_email(
        subject=subject,
        recipients=player_user.email,
        template='player_credentials',
        player=player_user.player,
        username=player_user.username,
        password=password,
        login_url=current_app.config.get('PLAYER_LOGIN_URL', '/player/login')
    )

def send_password_reset(user, token):
    """Send password reset instructions to a user.
    
    Args:
        user: Can be either a User or PlayerUser instance
        token: Password reset token
    """
    subject = "Password Reset Request"
    
    # Determine user type and set appropriate reset URL
    is_player = hasattr(user, 'player')  # Check if it's a PlayerUser
    base_url = current_app.config.get('PLAYER_BASE_URL' if is_player else 'BASE_URL', '')
    reset_url = f"{base_url}/reset_password/{token}"
    
    # Prepare user data for the email template
    user_data = {
        'name': user.username,  # All user types have username
        'email': user.email
    }
    
    # Add player-specific data if available
    if is_player and hasattr(user, 'player'):
        user_data['first_name'] = getattr(user.player, 'first_name', user.username)
    
    send_email(
        subject=subject,
        recipients=user.email,
        template='password_reset',
        user=user_data,
        reset_url=reset_url,
        token=token
    )

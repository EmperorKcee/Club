from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateTimeField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, EqualTo, ValidationError
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    remember_me = BooleanField('Remember Me')
    email = StringField('Email', validators=[Optional(), Email()])

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        from models import User, PlayerUser
        user = User.query.filter_by(email=email.data).first() or PlayerUser.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class AssignPlayerLoginForm(FlaskForm):
    player_id = SelectField('Player', coerce=int, validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create Account')

class TrainingSessionForm(FlaskForm):
    """Form for creating and editing training sessions"""
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    session_date = DateTimeField('Date & Time', 
                               format='%Y-%m-%dT%H:%M',
                               default=datetime.utcnow,
                               validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (minutes)', 
                                  default=90,
                                  validators=[DataRequired(), 
                                             NumberRange(min=15, max=240)])
    location = StringField('Location', default='Training Ground')
    session_type = SelectField('Session Type', 
                             choices=[
                                 ('training', 'Training'),
                                 ('tactical', 'Tactical'),
                                 ('physical', 'Physical'),
                                 ('recovery', 'Recovery'),
                                 ('match_prep', 'Match Preparation'),
                                 ('other', 'Other')
                             ],
                             default='training')
    is_mandatory = BooleanField('Mandatory', default=True)
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    coach_id = SelectField('Coach', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Session')
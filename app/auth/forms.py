from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import Required, Email, Length, EqualTo, Regexp
from ..models import User

class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(Form):
    email = StringField('Email', 
                        validators=[Required(), 
                                    Length(1, 64), 
                                    Email()])
    username = StringField('Username', 
                           validators=[Required(), 
                                       Length(1, 64), 
                                       Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
                                              'Usernames must have only letters, '
                                              'numbers, dots or underscores')])
    password = PasswordField('Password', 
                             validators=[Required(), 
                                         EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class ChangePasswordForm(Form):
    old_password = PasswordField('Old Password',
                                 validators=[Required()])
    new_password = PasswordField('New Password',
                                 validators=[Required(), EqualTo('new_password2', message='Passwords must match.')])
    new_password2 = PasswordField('Confirm New Password', 
                                  validators=[Required()])
    submit = SubmitField('Change Password')
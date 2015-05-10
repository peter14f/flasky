from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, login_required, logout_user, current_user
from . import auth
from .. import db
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ForgotPasswordForm, \
                   PasswordResetForm, ChangeEmailRequestForm
from ..email import send_mail

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        u = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(u)
        db.session.commit() # commit is needed because id only gets auto-generated after this
        token = u.generate_confirmation_token()
        send_mail(u.email, 'Confirm Your Account',
                  'auth/email/confirm', user=u, token=token)
        flash("A confirmation email has been sent to you by email.")
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated():
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')

@auth.route('/resend_confirmation')
@login_required
def resend_confirmation():
    u = current_user
    token = u.generate_confirmation_token()
    send_mail(u.email, 'Confirm Your Account',
              'auth/email/confirm', user=u, token=token)
    flash("A new confirmation email has been sent to you by email.")
    return redirect(url_for('main.index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Invalid password')
        else:
            current_user.password = form.new_password.data
            flash('Your password has been changed. Please Log in with the new password.')
        return redirect(url_for('auth.login'))
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous():
        return render_template('main.index')
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u is not None:
            token = u.generate_reset_token()
            send_mail(u.email, 'Reset Your Email',
                      'auth/email/reset_password', user=u, email=u.email, token=token)
            flash("A link to reset your password has been sent to you by email.")
            return redirect(url_for('main.index'))
        else:
            flash("No username was registered with this email")
            return redirect(url_for('password_reset_request'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return render_template('main.index')
    form = PasswordResetForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u is None:
            flash('Wrong email!')
            return redirect(url_for('auth.password_reset', token=token))
        if not u.reset_password(token, form.password.data):
            flash('Link to reset password has expired. Please try requesting another link to reset your password again!')
            return redirect(url_for('auth.password_reset_request'))

        flash('Password for username ' + "'" +
              u.username + "'" + " has been reset.")
        return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailRequestForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.password.data):
            flash("Wrong password!")
            return redirect(url_for('auth.change_email_request'))
        if not User.query.filter_by(email=form.newemail.data).first() is None:
            flash("You may not use this email because it's already registered with Flasky")
            return redirect(url_for('auth.change_email_request'))

        token = current_user.generate_email_change_token(form.newemail.data)
        send_mail(form.newemail.data, 'Change Email Registered with Flask',
                  'auth/email/change_email',
                  email=form.newemail.data, token=token)
        flash('A link to reset your email registered with Flasky has been mailed to ' + "'" + form.newemail.data + "'")
        return redirect(url_for('main.index'))
    return render_template('auth/change_email.html', form=form)

@auth.route('/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    if not current_user.change_email(token):
        flash('request failed... please make another email change request again.')
        return redirect(url_for('auth.change_email_request'))
    else:
        flash('Your email account registered with Flasky is successfully changed')
        return redirect(url_for('main.index'))
    return render_template('main/index.html')

from functools import wraps
from flask import abort, render_template
from flask.ext.login import current_user
from models import Permission

def permission_required(permissions):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_function(*args, **kwargs):
            if current_user.can(permissions):
                response = view_function(*args, **kwargs)
                return response
            else:
                return render_template('403.html'), 403
        return wrapped_function
    return decorator

def admin_required(view_function):
    return permission_required(Permission.ADMINISTER)(view_function)

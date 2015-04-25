from functools import wraps
from .errors import forbidden
from flask import g

def permission_required(permission):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_function(*args, **kwargs):
            if g.current_user.can(permission):
                response = view_function(*args, **kwargs)
                return response
            else:
                return forbidden('does not have permission')
        return wrapped_function
    return decorator
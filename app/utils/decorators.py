from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Restreint aux utilisateurs avec rôle tenant_admin ou superadmin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ('tenant_admin', 'superadmin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    """Restreint aux superadmins uniquement."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'superadmin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
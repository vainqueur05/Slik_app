from functools import wraps
from flask import request, abort
from flask_login import current_user

def get_tenant_slug():
    """
    Extrait le slug du tenant depuis l'URL.
    Suppose que le paramètre 'slug' est présent dans la route.
    """
    if request.view_args and 'slug' in request.view_args:
        return request.view_args['slug']
    return None

def tenant_required(f):
    """
    Décorateur pour les routes tenant admin.
    Vérifie que l'utilisateur connecté est autorisé à ce salon :
    - superadmin : toujours autorisé
    - tenant_admin : son tenant_slug doit correspondre au slug de l'URL
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        slug = get_tenant_slug()
        if not slug:
            abort(404)

        if not current_user.is_authenticated:
            abort(401)

        # Superadmin a tous les droits
        if current_user.role == 'superadmin':
            return f(*args, **kwargs)

        # Tenant admin doit correspondre
        if current_user.tenant_slug != slug:
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
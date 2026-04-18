from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return func(*args, **kwargs)

    return login_required(wrapped)

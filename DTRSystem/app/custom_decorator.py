from app import *
from functools import wraps


def login_is_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "index" not in session:
            return redirect(url_for('login_page'))
        else:
            pending_dict = display_pending()
            if pending_dict:
                session['pending'] = pending_dict
            return function(*args, **kwargs)

    return wrapper


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session['user_type'] != "Administrator":
            session['title'] = "403"
            return render_template("base/403.html")
        else:
            return function(*args, **kwargs)

    return wrapper


def clear_session(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if session.get('TOKEN'):
            logout_user(session.get('TOKEN'))
            session.clear()
        return f(*args, **kws)
    return decorated_function

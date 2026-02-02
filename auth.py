"""
Simple authentication system for Sunset Social
Protects dashboard and API endpoints with password
"""

from functools import wraps
from flask import session, redirect, url_for, request, render_template_string
import secrets


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def check_password(password, correct_password):
    """Check password securely"""
    return secrets.compare_digest(password, correct_password)


LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌅 Login - Sunset Social</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: rgba(22, 33, 62, 0.95);
            border: 2px solid #ff6b35;
            border-radius: 15px;
            padding: 2rem;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 10px 40px rgba(255, 107, 53, 0.3);
        }
        .login-card h2 {
            color: #ff6b35;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .btn-login {
            background: linear-gradient(135deg, #ff6b35, #ff85a2);
            border: none;
            width: 100%;
        }
        .alert {
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🌅 Sunset Social</h2>
        <p class="text-center text-light mb-4">Inserisci la password per accedere</p>

        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        <form method="POST" action="{{ url_for('login_page') }}">
            <input type="hidden" name="next" value="{{ next_url }}">
            <div class="mb-3">
                <input type="password" class="form-control" name="password"
                       placeholder="Password" required autofocus>
            </div>
            <button type="submit" class="btn btn-login btn-lg">
                🔓 Accedi
            </button>
        </form>

        <p class="text-center text-muted mt-4 small">
            Password configurabile in .env (ADMIN_PASSWORD)
        </p>
    </div>
</body>
</html>
"""

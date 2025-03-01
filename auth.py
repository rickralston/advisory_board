from flask import Blueprint, request, jsonify, session
from supabase import create_client, Client
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask Blueprint
auth_bp = Blueprint("auth", __name__)

# Connect to Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = "auth.login"

# User model
class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    """Loads user from session"""
    return User(user_id, session.get("email")) if "email" in session else None

# Signup Route
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return jsonify({"message": "Signup successful!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Login Route
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user_id = response.user.id

        # Save session data
        session["user_id"] = user_id
        session["email"] = email
        login_user(User(user_id, email))

        return jsonify({"message": "Login successful!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Logout Route
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    logout_user()
    return jsonify({"message": "Logged out successfully!"}), 200

# Protected Route Example
@auth_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return jsonify({"message": f"Welcome {current_user.email}!"})


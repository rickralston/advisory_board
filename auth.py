import os
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from supabase import create_client, Client

# Initialize Blueprint
auth_bp = Blueprint("auth", __name__)

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Secret key for JWT tokens (should be strong and stored securely)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 60  # Token expires in 1 hour

# Logging
logging.basicConfig(level=logging.INFO)


def generate_jwt(user_id):
    """Generate a JWT token for authentication"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """User signup using Supabase Auth"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Check if user already exists
    try:
        existing_user = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if existing_user:
            return jsonify({"error": "User already exists"}), 400
    except Exception:
        pass  # User does not exist, so we can proceed with signup

    # Sign up user
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        
        # Store user in the "users" table after successful signup
        supabase.table("users").insert({"id": user.user.id, "email": email}).execute()
        
        return jsonify({"message": "User created successfully", "user_id": user.user.id}), 201

    except Exception as e:
        logging.error(f"Signup error: {e}")
        return jsonify({"error": str(e)}), 500

        

@auth_bp.route("/login", methods=["POST"])
def login():
    """User login using Supabase Auth"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user and user.user:
            token = generate_jwt(user.user.id)
            return jsonify({"message": "Login successful", "token": token}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout user by invalidating the token (handled client-side)"""
    return jsonify({"message": "Logout successful"}), 200

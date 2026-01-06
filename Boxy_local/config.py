import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (parent of boxy2 folder)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

# Try multiple locations for .env file
# 1. Project root (preferred)
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✓ Loaded .env from: {env_path}")
else:
    # 2. Current working directory
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists():
        load_dotenv(dotenv_path=cwd_env)
        print(f"✓ Loaded .env from: {cwd_env}")
    else:
        # 3. Try default location (current directory)
        load_dotenv()
        print(f"⚠️ .env file not found at: {env_path}")
        print(f"   Please create .env file at: {env_path}")
        print(f"   You can copy .env.example from boxy2 folder as a template")

# Razorpay Configuration
# Replace these with your actual Razorpay Test API keys from https://dashboard.razorpay.com/app/keys

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'rzp_test_RwuSQ0jyjXIA9Y')  # Your Razorpay Test Key ID
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'zhpYi4nu8bddc6eXuvLIWmgQ')    # Your Razorpay Test Key Secret

# Note: Never commit real keys to version control
# For production, use environment variables in Render dashboard

# SMTP Email Configuration (Gmail)
# Set these environment variables:
# SMTP_EMAIL - Your Gmail address
# SMTP_PASSWORD - Gmail App Password (not regular password)
# To generate App Password: https://myaccount.google.com/apppasswords

SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'

# Debug: Print SMTP config status (remove in production)
if not SMTP_EMAIL or not SMTP_PASSWORD:
    print("⚠️ SMTP Configuration Status:")
    print(f"   SMTP_EMAIL: {'SET' if SMTP_EMAIL else 'NOT SET - Please set in .env file'}")
    print(f"   SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT SET - Please set in .env file'}")
    print(f"   .env file location: {env_path}")
    print(f"   .env file exists: {env_path.exists()}")

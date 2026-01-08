import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (parent of Boxy_local folder)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

# Try multiple locations for .env file
# 1. Project root (preferred)
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # 2. Current working directory
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists():
        load_dotenv(dotenv_path=cwd_env)
    else:
        # 3. Try default location (current directory)
        load_dotenv()

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

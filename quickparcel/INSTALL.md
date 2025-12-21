# Installation Guide

## Quick Fix for Missing Modules

### Install All Required Packages

**Option 1: Install all requirements at once (Recommended)**
```bash
pip install -r requirements.txt
```

**Option 2: Install packages individually**
```bash
# Install requests (for Google Distance Matrix API)
pip install requests

# Install MySQL connector
pip install mysql-connector-python

# Install Flask and dependencies
pip install Flask Werkzeug python-dotenv
```

**Option 3: Using pip3**
```bash
pip3 install -r requirements.txt
```

**Option 4: Using Python module installer**
```bash
python3 -m pip install -r requirements.txt
```

### Option 4: Using Python module installer
```bash
python3 -m pip install requests
```

### Option 5: Using Virtual Environment (Best Practice)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Verify Installation

After installing, verify all modules work:
```bash
# Test requests
python3 -c "import requests; print('✓ requests installed')"

# Test MySQL connector
python3 -c "import mysql.connector; print('✓ mysql-connector-python installed')"

# Test Flask
python3 -c "import flask; print('✓ Flask installed')"
```

## Common Errors and Solutions

### Error: "No module named 'requests'"
```bash
pip install requests
```

### Error: "No module named 'mysql'"
```bash
pip install mysql-connector-python
```

### Error: Permission Denied
Use virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Error: pip not found
Try:
```bash
python3 -m pip install -r requirements.txt
```

## If You Still Get Errors

1. **Permission Errors**: Use `sudo` (not recommended) or virtual environment
2. **Python Version**: Make sure you're using Python 3.10+
3. **Virtual Environment**: Always recommended for Python projects

## After Installation

Once `requests` is installed, you can run the Flask app:
```bash
python app.py
```

The app will work with or without Google API key:
- **With API key**: Real distance calculations
- **Without API key**: Estimated distances (5km per segment)


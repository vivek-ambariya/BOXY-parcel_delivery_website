# Render Deployment Guide - MySQL on Render

This guide will help you deploy your Boxy Flask application to Render with MySQL database.

## ✅ Code Changes Completed

The following files have been updated for production deployment:
- ✅ `Procfile` - Created for Render deployment
- ✅ `requirements.txt` - Added gunicorn
- ✅ `database.py` - Updated to use environment variables
- ✅ `app.py` - Updated for production settings
- ✅ `config.py` - Updated to use environment variables

## 📋 Deployment Steps

### Step 1: Push Code to GitHub

1. Initialize git (if not already done):
```bash
cd "/Users/ambariyavivek/vivek college/sem 3 project"
git init
git add .
git commit -m "Prepare for Render deployment"
```

2. Create a GitHub repository:
   - Go to https://github.com/new
   - Create a new repository (e.g., `boxy-app`)
   - Don't initialize with README

3. Push to GitHub:
```bash
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

### Step 2: Fork MySQL Template

1. Go to: https://github.com/render-examples/mysql
2. Click "Fork" button (top right)
3. This creates a copy in your GitHub account

### Step 3: Create MySQL Private Service on Render

1. Go to https://render.com and sign up/login
2. Click "New +" → "Private Service"
3. Connect your forked MySQL repository
4. Configure:
   - **Name**: `boxy-mysql`
   - **Environment**: `Docker`
   - **Region**: Choose closest to you
5. Add Environment Variables:
   ```
   MYSQL_DATABASE=boxy
   MYSQL_USER=boxy_user
   MYSQL_PASSWORD=<generate-strong-password>
   MYSQL_ROOT_PASSWORD=<generate-strong-password>
   ```
   **Tip**: Generate passwords using:
   ```bash
   python -c "import secrets; print(secrets.token_hex(16))"
   ```
6. Add Persistent Disk (in Advanced section):
   - **Name**: `mysql-data`
   - **Mount Path**: `/var/lib/mysql`
   - **Size**: `10 GB`
7. Click "Create Private Service"
8. Wait 2-3 minutes for deployment
9. **Note the service name** (should be `boxy-mysql`)

### Step 4: Create Web Service on Render

1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository (the one with your Flask app)
3. Configure:
   - **Name**: `boxy-app`
   - **Environment**: `Python 3`
   - **Region**: Same as MySQL service
   - **Branch**: `main`
   - **Root Directory**: `Boxy` (if your repo root is the parent folder)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Don't click "Create" yet!**

### Step 5: Add Environment Variables

In the web service setup page, scroll to "Environment Variables" and add:

```
DB_HOST=boxy-mysql
DB_NAME=boxy
DB_USER=boxy_user
DB_PASSWORD=<same-password-from-mysql-service>
DB_PORT=3306
RAZORPAY_KEY_ID=rzp_test_RwuSQ0jyjXIA9Y
RAZORPAY_KEY_SECRET=zhpYi4nu8bddc6eXuvLIWmgQ
SMTP_EMAIL=<your-gmail-address>
SMTP_PASSWORD=<your-gmail-app-password>
GOOGLE_API_KEY=<your-google-api-key-if-you-have-one>
SECRET_KEY=<generate-random-string>
ENVIRONMENT=production
```

**Important Notes:**
- `DB_HOST` must be exactly `boxy-mysql` (the name of your MySQL service)
- `DB_PASSWORD` must match the `MYSQL_PASSWORD` you set in MySQL service
- Generate `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- For `SMTP_PASSWORD`, use Gmail App Password (not regular password):
  - Go to https://myaccount.google.com/apppasswords
  - Generate app password for "Mail"
  - Use the 16-character password

### Step 6: Deploy

1. Click "Create Web Service"
2. Render will start building (takes 3-5 minutes)
3. Watch the build logs for any errors
4. Once deployed, your app will be live at: `https://boxy-app.onrender.com`

### Step 7: Initialize Database

On first deployment, your app will automatically create database tables via `init_database()` function. Check the logs to confirm tables were created successfully.

## 🔍 Troubleshooting

### Database Connection Errors

1. Verify `DB_HOST` matches your MySQL service name exactly
2. Check that MySQL service is running (green status)
3. Ensure passwords match between MySQL service and web service
4. Check Render logs for connection errors

### Build Failures

1. Check that `requirements.txt` includes all dependencies
2. Verify Python version compatibility
3. Check build logs for specific error messages

### Static Files Not Loading

1. Ensure `static/` folder is in your repository
2. Check that templates use `url_for('static', ...)` for static files
3. Verify file paths are correct

### App Not Starting

1. Check runtime logs in Render dashboard
2. Verify `Procfile` is correct
3. Ensure `gunicorn` is in `requirements.txt`
4. Check that `PORT` environment variable is set (Render sets this automatically)

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | MySQL service name | `boxy-mysql` |
| `DB_NAME` | Database name | `boxy` |
| `DB_USER` | Database username | `boxy_user` |
| `DB_PASSWORD` | Database password | `<your-password>` |
| `DB_PORT` | Database port | `3306` |
| `RAZORPAY_KEY_ID` | Razorpay API key | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | `<your-secret>` |
| `SMTP_EMAIL` | Gmail address | `your@gmail.com` |
| `SMTP_PASSWORD` | Gmail app password | `<16-char-password>` |
| `GOOGLE_API_KEY` | Google Maps API key | `<optional>` |
| `SECRET_KEY` | Flask secret key | `<random-32-char>` |
| `ENVIRONMENT` | Environment type | `production` |

## 🎯 Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Forked MySQL template repository
- [ ] Created MySQL Private Service on Render
- [ ] Added persistent disk to MySQL service
- [ ] Created Web Service on Render
- [ ] Added all environment variables
- [ ] Deployed both services
- [ ] Tested the application
- [ ] Verified database tables created

## 🔗 Useful Links

- Render Dashboard: https://dashboard.render.com
- MySQL Template: https://github.com/render-examples/mysql
- Render Docs: https://render.com/docs
- Gmail App Passwords: https://myaccount.google.com/apppasswords

## 📞 Need Help?

If you encounter issues:
1. Check Render build logs
2. Check Render runtime logs
3. Verify all environment variables are set correctly
4. Ensure MySQL service is running and accessible

Good luck with your deployment! 🚀


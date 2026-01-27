# Render Deployment Guide - PostgreSQL on Render

This guide will help you deploy your Boxy Flask application to Render with PostgreSQL database (FREE!).

## ✅ Code Changes Completed

The following files have been updated for production deployment with PostgreSQL:
- ✅ `Procfile` - Created for Render deployment
- ✅ `requirements.txt` - Added gunicorn and psycopg2-binary (PostgreSQL adapter)
- ✅ `database.py` - Converted from MySQL to PostgreSQL
- ✅ `app.py` - Updated for PostgreSQL compatibility
- ✅ `config.py` - Updated to use environment variables

## 📋 Deployment Steps

### Step 1: Push Code to GitHub

1. Initialize git (if not already done):
```bash
cd "/Users/ambariyavivek/vivek college/sem 3 project"
git add .
git commit -m "Convert to PostgreSQL for Render deployment"
git push
```

### Step 2: Create PostgreSQL Database on Render

1. Go to https://render.com and sign up/login
2. Click "New +" → "Postgres"
3. Configure:
   - **Name**: `boxy-db`
   - **Database**: `boxy`
   - **User**: `boxy_user` (or leave default)
   - **Region**: Choose closest to you
   - **PostgreSQL Version**: Latest
   - **Plan**: **Free** (this is free!)
4. Click "Create Database"
5. Wait 2-3 minutes for creation
6. **Note the connection details** (you'll need them in Step 4)

### Step 3: Create Web Service on Render

1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your GitHub repository: `vivek-ambariya/BOXY-parcel_delivery_website`
3. Configure:
   - **Name**: `boxy-app`
   - **Environment**: `Python 3`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `Boxy` (if your repo root is the parent folder)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. **Don't click "Create" yet!**

### Step 4: Add Environment Variables

In the web service setup page, scroll to "Environment Variables" and add:

```
DB_HOST=<from-postgres-database-dashboard>
DB_NAME=boxy
DB_USER=<from-postgres-database-dashboard>
DB_PASSWORD=<from-postgres-database-dashboard>
DB_PORT=5432
RAZORPAY_KEY_ID=rzp_test_RwuSQ0jyjXIA9Y
RAZORPAY_KEY_SECRET=zhpYi4nu8bddc6eXuvLIWmgQ
SMTP_EMAIL=<your-gmail-address>
SMTP_PASSWORD=<your-gmail-app-password>
GOOGLE_API_KEY=<your-google-api-key-if-you-have-one>
SECRET_KEY=<generate-random-string>
ENVIRONMENT=production
```

**How to get database values:**
1. Go to your PostgreSQL database dashboard on Render
2. Click on "Connections" tab
3. Copy the values for:
   - **Internal Database URL** (contains host, user, password, database)
   - Or use individual values:
     - Host (e.g., `dpg-xxxxx-a.singapore-postgres.render.com`)
     - Port: `5432`
     - Database: `boxy`
     - User: (from connection string)
     - Password: (from connection string)

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**For SMTP_PASSWORD:**
- Go to https://myaccount.google.com/apppasswords
- Generate app password for "Mail"
- Use the 16-character password (not your regular Gmail password)

### Step 5: Link Database to Web Service (Optional but Recommended)

1. In your web service environment variables section
2. Click "Link Database" or "Add from Database"
3. Select your `boxy-db` PostgreSQL database
4. Render will automatically add `DATABASE_URL` or individual connection variables

### Step 6: Deploy

1. Click "Create Web Service"
2. Render will start building (takes 3-5 minutes)
3. Watch the build logs for any errors
4. Once deployed, your app will be live at: `https://boxy-app.onrender.com`

### Step 7: Initialize Database

On first deployment, your app will automatically create database tables via `init_database()` function. Check the logs to confirm tables were created successfully.

## 🔍 Troubleshooting

### Database Connection Errors

1. Verify `DB_HOST` matches your PostgreSQL database hostname
2. Check that PostgreSQL database is running (green status)
3. Ensure passwords match
4. Verify `DB_PORT` is `5432` (PostgreSQL default)
5. Check Render logs for connection errors

### Build Failures

1. Check that `requirements.txt` includes `psycopg2-binary`
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
| `DB_HOST` | PostgreSQL hostname | `dpg-xxxxx-a.singapore-postgres.render.com` |
| `DB_NAME` | Database name | `boxy` |
| `DB_USER` | Database username | `boxy_user` |
| `DB_PASSWORD` | Database password | `<from-render>` |
| `DB_PORT` | Database port | `5432` |
| `RAZORPAY_KEY_ID` | Razorpay API key | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | Razorpay secret | `<your-secret>` |
| `SMTP_EMAIL` | Gmail address | `your@gmail.com` |
| `SMTP_PASSWORD` | Gmail app password | `<16-char-password>` |
| `GOOGLE_API_KEY` | Google Maps API key | `<optional>` |
| `SECRET_KEY` | Flask secret key | `<random-32-char>` |
| `ENVIRONMENT` | Environment type | `production` |

## 🎯 Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Created PostgreSQL database on Render (FREE!)
- [ ] Created Web Service on Render
- [ ] Added all environment variables
- [ ] Linked database to web service (optional)
- [ ] Deployed successfully
- [ ] Tested the application
- [ ] Verified database tables created

## 💰 Cost

- **PostgreSQL Database**: FREE (on Render's free tier)
- **Web Service**: FREE (on Render's free tier)
- **Total Cost**: $0/month! 🎉

## 🔗 Useful Links

- Render Dashboard: https://dashboard.render.com
- Render Docs: https://render.com/docs
- Gmail App Passwords: https://myaccount.google.com/apppasswords
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## 📞 Need Help?

If you encounter issues:
1. Check Render build logs
2. Check Render runtime logs
3. Verify all environment variables are set correctly
4. Ensure PostgreSQL database is running and accessible

Good luck with your deployment! 🚀

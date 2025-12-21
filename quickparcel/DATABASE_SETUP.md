# Database Setup Guide for Boxy

## Prerequisites
- XAMPP installed and running
- MySQL service started in XAMPP

## Database Configuration

The application uses MySQL database named **Boxy** from XAMPP.

### Default Configuration:
- **Host**: localhost
- **Database**: Boxy
- **User**: root
- **Password**: (empty - default XAMPP)
- **Port**: 3306

## Setup Steps

### 1. Start XAMPP MySQL
- Open XAMPP Control Panel
- Start MySQL service

### 2. Create Database (Optional - Auto-created)
The application will automatically create the database and tables on first run.

OR manually create using phpMyAdmin:
1. Open phpMyAdmin (http://localhost/phpmyadmin)
2. Create database named `Boxy`
3. Import `database_schema.sql` file

### 3. Update Database Configuration (if needed)
If your MySQL has a different password, edit `database.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Boxy',
    'user': 'root',
    'password': 'your_password_here',  # Update if needed
    'port': 3306
}
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python app.py
```

The application will automatically:
- Connect to MySQL database
- Create tables if they don't exist
- Initialize the database schema

## Database Schema

### Partners Table
- Stores delivery partner information
- Fields: id, name, phone, email, vehicle details, status, etc.

### Deliveries Table
- Stores parcel delivery information
- Fields: id, sender/receiver details, status, partner assignment, timestamps

## Troubleshooting

### Connection Error
- Ensure MySQL is running in XAMPP
- Check if database name is correct
- Verify username and password

### Table Creation Error
- Check MySQL user permissions
- Ensure database exists
- Check MySQL version compatibility

### Import SQL File
If auto-creation fails, manually import `database_schema.sql`:
1. Open phpMyAdmin
2. Select `Boxy` database
3. Go to Import tab
4. Choose `database_schema.sql` file
5. Click Go


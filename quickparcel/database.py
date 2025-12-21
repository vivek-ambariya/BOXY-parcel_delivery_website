try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("WARNING: mysql-connector-python not installed. Please run: pip install mysql-connector-python")
    # Create dummy Error class for type hints
    class Error(Exception):
        pass

from contextlib import contextmanager

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Boxy',
    'user': 'root',
    'password': '',  # Default XAMPP MySQL password is empty
    'port': 3306
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create partners table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS partners (
                    id VARCHAR(20) PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    vehicle_type VARCHAR(50) NOT NULL,
                    vehicle_number VARCHAR(50) NOT NULL,
                    aadhar VARCHAR(20) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    status ENUM('online', 'offline') DEFAULT 'offline',
                    approved BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_status (status)
                )
            """)
            
            # Create deliveries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id VARCHAR(20) PRIMARY KEY,
                    sender_name VARCHAR(100) NOT NULL,
                    sender_address TEXT NOT NULL,
                    receiver_name VARCHAR(100) NOT NULL,
                    receiver_address TEXT NOT NULL,
                    receiver_phone VARCHAR(20) NOT NULL,
                    parcel_type VARCHAR(50) NOT NULL,
                    weight DECIMAL(5,2) NOT NULL,
                    status ENUM('available', 'accepted', 'picked', 'on_the_way', 'delivered') DEFAULT 'available',
                    partner_id VARCHAR(20) NULL,
                    total_stops INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP NULL,
                    updated_at TIMESTAMP NULL,
                    delivered_at TIMESTAMP NULL,
                    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE SET NULL,
                    INDEX idx_status (status),
                    INDEX idx_partner (partner_id)
                )
            """)
            
            # Create delivery_stops table (Multi-Stop Feature)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivery_stops (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id VARCHAR(20) NOT NULL,
                    stop_number INT NOT NULL,
                    drop_address TEXT NOT NULL,
                    receiver_name VARCHAR(100) NOT NULL,
                    receiver_phone VARCHAR(20) NOT NULL,
                    status ENUM('pending', 'delivered') DEFAULT 'pending',
                    delivered_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES deliveries(id) ON DELETE CASCADE,
                    INDEX idx_booking (booking_id),
                    INDEX idx_status (status),
                    UNIQUE KEY unique_stop (booking_id, stop_number)
                )
            """)
            
            conn.commit()
            print("Database tables initialized successfully!")
            
    except Error as e:
        print(f"Error initializing database: {e}")


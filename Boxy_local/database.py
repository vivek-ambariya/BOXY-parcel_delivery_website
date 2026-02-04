import sys
sys.stdout.reconfigure(encoding='utf-8')

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
                    status ENUM('available', 'accepted', 'picked', 'on_the_way', 'delivered', 'completed') DEFAULT 'available',
                    partner_id VARCHAR(20) NULL,
                    total_stops INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP NULL,
                    updated_at TIMESTAMP NULL,
                    delivered_at TIMESTAMP NULL,
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    payment_status ENUM('pending', 'paid', 'pending_cash') DEFAULT 'pending',
                    payment_method ENUM('online', 'cash') NULL,
                    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE SET NULL,
                    INDEX idx_status (status),
                    INDEX idx_partner (partner_id),
                    INDEX idx_payment_status (payment_status)
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
            
            # Check and add missing columns to existing tables (migrations)
            # Add total_stops column if it doesn't exist
            try:
                cursor.execute("SHOW COLUMNS FROM deliveries LIKE 'total_stops'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE deliveries ADD COLUMN total_stops INT DEFAULT 1 AFTER partner_id")
                    conn.commit()
                    print(" Added 'total_stops' column to deliveries table")
                else:
                    print(" Column 'total_stops' already exists in deliveries table")
            except Error as e:
                # If table doesn't exist yet, that's okay - it will be created above
                if "doesn't exist" not in str(e).lower():
                    print(f"Note: Could not check/add total_stops column: {e}")
            
            # Add payment columns if they don't exist
            try:
                cursor.execute("SHOW COLUMNS FROM deliveries LIKE 'payment_status'")
                if not cursor.fetchone():
                    # Add columns one by one to avoid issues
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN total_amount DECIMAL(10,2) DEFAULT 0.00 AFTER delivered_at")
                        conn.commit()
                        print("✓ Added 'total_amount' column")
                    except Error as e:
                        if "Duplicate column name" not in str(e):
                            print(f"Note adding total_amount: {e}")
                    
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN payment_status ENUM('pending', 'paid', 'pending_cash') DEFAULT 'pending' AFTER total_amount")
                        conn.commit()
                        print("✓ Added 'payment_status' column")
                    except Error as e:
                        if "Duplicate column name" not in str(e):
                            print(f"Note adding payment_status: {e}")
                    
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN payment_method ENUM('online', 'cash') NULL DEFAULT NULL AFTER payment_status")
                        conn.commit()
                        print("✓ Added 'payment_method' column")
                    except Error as e:
                        if "Duplicate column name" not in str(e):
                            print(f"Note adding payment_method: {e}")
                    
                    print("✓ Added payment columns to deliveries table")
                else:
                    print("✓ Payment columns already exist in deliveries table")
            except Error as e:
                if "doesn't exist" not in str(e).lower():
                    print(f"Note: Could not check/add payment columns: {e}")
            
            # Add parcel details columns (specification, dimensions, preferred vehicle) if they don't exist
            for col_name, col_def in [
                ('parcel_type_specification', 'TEXT NULL'),
                ('parcel_height', 'DECIMAL(5,2) NULL'),
                ('parcel_width', 'DECIMAL(5,2) NULL'),
                ('preferred_vehicle', 'VARCHAR(20) NULL'),
            ]:
                try:
                    cursor.execute(f"SHOW COLUMNS FROM deliveries LIKE '{col_name}'")
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE deliveries ADD COLUMN {col_name} {col_def} AFTER weight")
                        conn.commit()
                        print(f" Added '{col_name}' to deliveries table")
                except Error as e:
                    if "Duplicate column name" not in str(e):
                        print(f"Note adding {col_name}: {e}")
            
            # Check and update status ENUM to include 'completed' if it doesn't
            try:
                # Use information_schema to check current ENUM values
                cursor.execute("""
                    SELECT COLUMN_TYPE 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'deliveries' 
                    AND COLUMN_NAME = 'status'
                """)
                result = cursor.fetchone()
                if result:
                    enum_type = result[0] if isinstance(result, tuple) else result.get('COLUMN_TYPE', '')
                    if 'completed' not in enum_type:
                        # Modify the ENUM to include 'completed'
                        cursor.execute("""
                            ALTER TABLE deliveries 
                            MODIFY COLUMN status ENUM('available', 'accepted', 'picked', 'on_the_way', 'delivered', 'completed') 
                            DEFAULT 'available'
                        """)
                        conn.commit()
                        print("✓ Updated status ENUM to include 'completed'")
                    else:
                        print("✓ Status ENUM already includes 'completed'")
            except Error as e:
                if "doesn't exist" not in str(e).lower():
                    print(f"Note: Could not check/update status ENUM: {e}")
            
            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id VARCHAR(20) PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_customer_email (email),
                    INDEX idx_customer_phone (phone)
                )
            """)
            
            # Check and fix id column type if it's integer (migration)
            try:
                cursor.execute("""
                    SELECT DATA_TYPE 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'customers' 
                    AND COLUMN_NAME = 'id'
                """)
                result = cursor.fetchone()
                if result:
                    data_type = result[0] if isinstance(result, tuple) else result.get('DATA_TYPE', '')
                    if data_type in ['int', 'bigint', 'integer']:
                        print("⚠️ Found customers.id as integer type, migrating to VARCHAR...")
                        
                        # Check if table has any data
                        cursor.execute("SELECT COUNT(*) as count FROM customers")
                        count_result = cursor.fetchone()
                        row_count = count_result[0] if isinstance(count_result, tuple) else count_result.get('count', 0)
                        
                        if row_count > 0:
                            print(f"⚠️ Table has {row_count} rows. Converting integer IDs to VARCHAR format...")
                            # Get all rows and update IDs
                            cursor.execute("SELECT * FROM customers")
                            rows = cursor.fetchall()
                            
                            # Create temporary table with correct schema
                            cursor.execute("""
                                CREATE TABLE customers_temp (
                                    id VARCHAR(20) PRIMARY KEY,
                                    first_name VARCHAR(100) NOT NULL,
                                    last_name VARCHAR(100) NOT NULL,
                                    email VARCHAR(100) UNIQUE NOT NULL,
                                    phone VARCHAR(20) UNIQUE NOT NULL,
                                    address TEXT NOT NULL,
                                    password VARCHAR(255) NOT NULL,
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    INDEX idx_customer_email (email),
                                    INDEX idx_customer_phone (phone)
                                )
                            """)
                            
                            # Migrate data with converted IDs
                            for row in rows:
                                old_id = row[0] if isinstance(row, tuple) else row.get('id')
                                new_id = f"CUST{int(old_id):04d}" if isinstance(old_id, (int, str)) and str(old_id).isdigit() else str(old_id)
                                
                                if isinstance(row, tuple):
                                    cursor.execute("""
                                        INSERT INTO customers_temp (id, first_name, last_name, email, phone, address, password, created_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (new_id, row[1], row[2], row[3], row[4], row[5], row[6], row[7] if len(row) > 7 else None))
                                else:
                                    cursor.execute("""
                                        INSERT INTO customers_temp (id, first_name, last_name, email, phone, address, password, created_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """, (new_id, row.get('first_name'), row.get('last_name'), row.get('email'), 
                                          row.get('phone'), row.get('address'), row.get('password'), row.get('created_at')))
                            
                            # Drop old table and rename new one
                            cursor.execute("DROP TABLE customers")
                            cursor.execute("RENAME TABLE customers_temp TO customers")
                            print(f"✓ Successfully migrated {row_count} customer records to VARCHAR IDs")
                        else:
                            # No data, just alter the column
                            try:
                                cursor.execute("ALTER TABLE customers DROP PRIMARY KEY")
                            except Error as e:
                                if "doesn't exist" not in str(e).lower():
                                    print(f"Note: Could not drop primary key: {e}")
                            
                            cursor.execute("ALTER TABLE customers MODIFY COLUMN id VARCHAR(20) NOT NULL")
                            cursor.execute("ALTER TABLE customers ADD PRIMARY KEY (id)")
                            print("✓ Successfully migrated customers.id to VARCHAR(20)")
                        
                        conn.commit()
                    else:
                        print("✓ customers.id column type is correct (VARCHAR)")
            except Error as e:
                if "doesn't exist" not in str(e).lower():
                    print(f"Note: Could not check/fix customers.id column type: {e}")
            
            # Create password_reset_tokens table (stores OTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    token VARCHAR(255) NOT NULL,
                    otp VARCHAR(4) NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_token (token),
                    INDEX idx_otp (otp),
                    INDEX idx_expires (expires_at)
                )
            """)
            
            # Create email_verification table (stores registration OTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_verification (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    otp VARCHAR(4) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_otp (otp),
                    INDEX idx_expires (expires_at)
                )
            """)
            
            # Add OTP column if table exists but column doesn't
            try:
                cursor.execute("SHOW COLUMNS FROM password_reset_tokens LIKE 'otp'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE password_reset_tokens ADD COLUMN otp VARCHAR(4) NULL AFTER token")
                    conn.commit()
                    print("✓ Added 'otp' column to password_reset_tokens table")
            except Error as e:
                if "doesn't exist" not in str(e).lower():
                    print(f"Note: Could not check/add otp column: {e}")
            
            conn.commit()
            print("✓ Database tables initialized successfully!")
            
    except Error as e:
        print(f"Error initializing database: {e}")


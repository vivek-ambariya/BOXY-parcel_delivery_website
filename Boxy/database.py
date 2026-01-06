try:
    import psycopg2
    from psycopg2 import Error
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("WARNING: psycopg2-binary not installed. Please run: pip install psycopg2-binary")
    # Create dummy Error class for type hints
    class Error(Exception):
        pass
    RealDictCursor = None

from contextlib import contextmanager
import os

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'Boxy'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', '5432'))
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_dict_cursor(conn):
    """Get a dictionary cursor for PostgreSQL"""
    return conn.cursor(cursor_factory=RealDictCursor)

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
                    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline')),
                    approved BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for partners
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON partners(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON partners(status)")
            
            # Create deliveries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deliveries (
                    id VARCHAR(20) PRIMARY KEY,
                    sender_name VARCHAR(100) NOT NULL,
                    sender_address TEXT NOT NULL,
                    sender_email VARCHAR(255),
                    receiver_name VARCHAR(100) NOT NULL,
                    receiver_address TEXT NOT NULL,
                    receiver_phone VARCHAR(20) NOT NULL,
                    parcel_type VARCHAR(50) NOT NULL,
                    weight DECIMAL(5,2) NOT NULL,
                    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'accepted', 'picked', 'on_the_way', 'delivered', 'completed')),
                    partner_id VARCHAR(20),
                    total_stops INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TIMESTAMP NULL,
                    updated_at TIMESTAMP NULL,
                    delivered_at TIMESTAMP NULL,
                    total_amount DECIMAL(10,2) DEFAULT 0.00,
                    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'pending_cash')),
                    payment_method VARCHAR(20) CHECK (payment_method IN ('online', 'cash')),
                    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE SET NULL
                )
            """)
            
            # Create indexes for deliveries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON deliveries(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_partner ON deliveries(partner_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_status ON deliveries(payment_status)")
            
            # Create delivery_stops table (Multi-Stop Feature)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delivery_stops (
                    id SERIAL PRIMARY KEY,
                    booking_id VARCHAR(20) NOT NULL,
                    stop_number INT NOT NULL,
                    drop_address TEXT NOT NULL,
                    receiver_name VARCHAR(100) NOT NULL,
                    receiver_phone VARCHAR(20) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'delivered')),
                    delivered_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES deliveries(id) ON DELETE CASCADE,
                    UNIQUE (booking_id, stop_number)
                )
            """)
            
            # Create indexes for delivery_stops
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_booking ON delivery_stops(booking_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON delivery_stops(status)")
            
            # Check and add missing columns to existing tables (migrations)
            # Add total_stops column if it doesn't exist
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'deliveries' AND column_name = 'total_stops'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE deliveries ADD COLUMN total_stops INT DEFAULT 1")
                    conn.commit()
                    print("✓ Added 'total_stops' column to deliveries table")
                else:
                    print("✓ Column 'total_stops' already exists in deliveries table")
            except Error as e:
                if "does not exist" not in str(e).lower():
                    print(f"Note: Could not check/add total_stops column: {e}")
            
            # Add payment columns if they don't exist
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'deliveries' AND column_name = 'payment_status'
                """)
                if not cursor.fetchone():
                    # Add columns one by one to avoid issues
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN total_amount DECIMAL(10,2) DEFAULT 0.00")
                        conn.commit()
                        print("✓ Added 'total_amount' column")
                    except Error as e:
                        if "already exists" not in str(e).lower():
                            print(f"Note adding total_amount: {e}")
                    
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'pending_cash'))")
                        conn.commit()
                        print("✓ Added 'payment_status' column")
                    except Error as e:
                        if "already exists" not in str(e).lower():
                            print(f"Note adding payment_status: {e}")
                    
                    try:
                        cursor.execute("ALTER TABLE deliveries ADD COLUMN payment_method VARCHAR(20) CHECK (payment_method IN ('online', 'cash'))")
                        conn.commit()
                        print("✓ Added 'payment_method' column")
                    except Error as e:
                        if "already exists" not in str(e).lower():
                            print(f"Note adding payment_method: {e}")
                    
                    print("✓ Added payment columns to deliveries table")
                else:
                    print("✓ Payment columns already exist in deliveries table")
            except Error as e:
                if "does not exist" not in str(e).lower():
                    print(f"Note: Could not check/add payment columns: {e}")
            
            # Add sender_email column if it doesn't exist
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'deliveries' AND column_name = 'sender_email'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE deliveries ADD COLUMN sender_email VARCHAR(255)")
                    conn.commit()
                    print("✓ Added 'sender_email' column")
            except Error as e:
                if "does not exist" not in str(e).lower():
                    print(f"Note: Could not check/add sender_email column: {e}")
            
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for customers
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_email ON customers(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_phone ON customers(phone)")
            
            # Create password_reset_tokens table (stores OTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    token VARCHAR(255) NOT NULL,
                    otp VARCHAR(4),
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for password_reset_tokens
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON password_reset_tokens(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_token ON password_reset_tokens(token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp ON password_reset_tokens(otp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires ON password_reset_tokens(expires_at)")
            
            # Create email_verification table (stores registration OTP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_verification (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    otp VARCHAR(4) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for email_verification
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_email ON email_verification(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp ON email_verification(otp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expires ON email_verification(expires_at)")
            
            # Add OTP column if table exists but column doesn't
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'password_reset_tokens' AND column_name = 'otp'
                """)
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE password_reset_tokens ADD COLUMN otp VARCHAR(4)")
                    conn.commit()
                    print("✓ Added 'otp' column to password_reset_tokens table")
            except Error as e:
                if "does not exist" not in str(e).lower():
                    print(f"Note: Could not check/add otp column: {e}")
            
            conn.commit()
            print("✓ Database tables initialized successfully!")
            
    except Error as e:
        print(f"Error initializing database: {e}")

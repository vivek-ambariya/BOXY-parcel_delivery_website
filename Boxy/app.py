from flask import Flask, render_template, request, jsonify, session, make_response
import secrets
import os
import requests
import hashlib
import hmac
import csv
import io
from datetime import datetime
from database import get_db_connection, init_database
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from email_service import send_confirmation_email, send_tracking_update, send_payment_receipt

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Initialize database on startup
init_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/send-parcel')
def send_parcel():
    return render_template('send_parcel.html')

@app.route('/track-parcel')
def track_parcel():
    return render_template('track_parcel.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/partner')
def partner():
    return render_template('partner.html')

# API Routes for Partner Operations
@app.route('/api/partner/register', methods=['POST'])
def partner_register():
    try:
        data = request.json
        
        # Generate partner ID
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM partners")
            count = cursor.fetchone()[0]
            partner_id = f"PARTNER{count + 1:04d}"
            
            # Check if email already exists
            cursor.execute("SELECT id FROM partners WHERE email = %s", (data.get('email'),))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            
            # Insert new partner
            cursor.execute("""
                INSERT INTO partners (id, first_name, last_name, phone, email, vehicle_type, 
                                   vehicle_number, aadhar, password, status, approved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'offline', TRUE)
            """, (
                partner_id,
                data.get('firstName'),
                data.get('lastName'),
                data.get('phone'),
                data.get('email'),
                data.get('vehicleType'),
                data.get('vehicleNumber'),
                data.get('aadhar'),
                data.get('password')
            ))
            
            conn.commit()
            
            return jsonify({
                'success': True, 
                'partner_id': partner_id, 
                'message': 'Registration successful!'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/partner/login', methods=['POST'])
def partner_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, first_name, last_name, phone, email, vehicle_type, 
                       vehicle_number, aadhar, status, approved
                FROM partners 
                WHERE (email = %s OR phone = %s) AND password = %s
            """, (email, email, password))
            
            partner = cursor.fetchone()
            
            if partner:
                partner['name'] = f"{partner['first_name']} {partner['last_name']}"
                session['partner_id'] = partner['id']
                return jsonify({'success': True, 'partner': partner})
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/partner/logout', methods=['POST'])
def partner_logout():
    session.pop('partner_id', None)
    return jsonify({'success': True})

@app.route('/api/partner/status', methods=['GET', 'POST'])
def partner_status():
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            print(f"DEBUG: No partner_id in session. Session: {dict(session)}")
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            if request.method == 'POST':
                data = request.json
                if not data:
                    return jsonify({'success': False, 'message': 'No data provided'}), 400
                
                new_status = data.get('status', 'offline')
                print(f"DEBUG: Updating partner {partner_id} status to {new_status}")
                
                # Update status in database
                cursor.execute("""
                    UPDATE partners SET status = %s WHERE id = %s
                """, (new_status, partner_id))
                
                # Check if update was successful
                rows_affected = cursor.rowcount
                print(f"DEBUG: Rows affected: {rows_affected}")
                
                if rows_affected == 0:
                    return jsonify({'success': False, 'message': 'Partner not found or no changes made'}), 404
                
                conn.commit()
                print(f"DEBUG: Status updated successfully to {new_status}")
            
            # Get current status
            cursor.execute("SELECT status FROM partners WHERE id = %s", (partner_id,))
            result = cursor.fetchone()
            
            if result:
                print(f"DEBUG: Current status from DB: {result['status']}")
                return jsonify({'success': True, 'status': result['status']})
            else:
                return jsonify({'success': False, 'message': 'Partner not found'}), 404
    except Exception as e:
        print(f"ERROR in partner_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/partner/deliveries', methods=['GET'])
def get_partner_deliveries():
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get partner's deliveries
            cursor.execute("""
                SELECT id, sender_name, sender_address, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id, total_stops,
                       created_at, accepted_at, updated_at, delivered_at,
                       total_amount, payment_status, payment_method
                FROM deliveries 
                WHERE partner_id = %s
                ORDER BY created_at DESC
            """, (partner_id,))
            partner_deliveries = cursor.fetchall()
            
            # Get stops for partner deliveries
            for delivery in partner_deliveries:
                delivery_id = delivery['id']
                cursor.execute("""
                    SELECT stop_number, drop_address, receiver_name, receiver_phone, status, delivered_at
                    FROM delivery_stops
                    WHERE booking_id = %s
                    ORDER BY stop_number
                """, (delivery_id,))
                delivery['stops'] = cursor.fetchall()
                # Convert datetime objects to strings
                for stop in delivery['stops']:
                    for key, value in stop.items():
                        if isinstance(value, datetime):
                            stop[key] = value.isoformat()
            
            # Convert datetime objects to strings for deliveries
            for delivery in partner_deliveries:
                for key, value in delivery.items():
                    if isinstance(value, datetime):
                        delivery[key] = value.isoformat()
            
            # Get available deliveries
            cursor.execute("""
                SELECT id, sender_name, sender_address, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id, total_stops,
                       created_at, accepted_at, updated_at, delivered_at
                FROM deliveries 
                WHERE status = 'available'
                ORDER BY created_at DESC
            """)
            available_deliveries = cursor.fetchall()
            
            # Get stops for available deliveries
            for delivery in available_deliveries:
                delivery_id = delivery['id']
                cursor.execute("""
                    SELECT stop_number, drop_address, receiver_name, receiver_phone, status
                    FROM delivery_stops
                    WHERE booking_id = %s
                    ORDER BY stop_number
                """, (delivery_id,))
                delivery['stops'] = cursor.fetchall()
            
            # Convert datetime objects to strings
            for delivery in available_deliveries:
                for key, value in delivery.items():
                    if isinstance(value, datetime):
                        delivery[key] = value.isoformat()
            
            return jsonify({
                'success': True,
                'my_deliveries': partner_deliveries,
                'available_deliveries': available_deliveries
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/partner/accept-delivery', methods=['POST'])
def accept_delivery():
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if partner is online
            cursor.execute("SELECT status FROM partners WHERE id = %s", (partner_id,))
            partner = cursor.fetchone()
            if not partner or partner['status'] != 'online':
                return jsonify({'success': False, 'message': 'You must be online to accept deliveries'}), 400
            
            data = request.json
            delivery_id = data.get('delivery_id')
            
            # Check if delivery exists and is available
            cursor.execute("""
                SELECT id, status FROM deliveries WHERE id = %s
            """, (delivery_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404
            
            if delivery['status'] != 'available':
                return jsonify({'success': False, 'message': 'Delivery is no longer available'}), 400
            
            # Assign delivery to partner
            cursor.execute("""
                UPDATE deliveries 
                SET partner_id = %s, status = 'accepted', accepted_at = NOW()
                WHERE id = %s
            """, (partner_id, delivery_id))
            conn.commit()
            
            # Get updated delivery with sender_email
            cursor.execute("""
                SELECT id, sender_name, sender_address, sender_email, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id, total_stops,
                       created_at, accepted_at, updated_at, delivered_at
                FROM deliveries WHERE id = %s
            """, (delivery_id,))
            updated_delivery = cursor.fetchone()
            
            # Get partner name if partner_id exists
            partner_name = None
            if updated_delivery.get('partner_id'):
                cursor.execute("""
                    SELECT first_name, last_name FROM partners WHERE id = %s
                """, (updated_delivery['partner_id'],))
                partner = cursor.fetchone()
                if partner:
                    partner_name = f"{partner['first_name']} {partner['last_name']}"
            
            # Get stops
            cursor.execute("""
                SELECT stop_number, drop_address, receiver_name, receiver_phone, status, delivered_at
                FROM delivery_stops
                WHERE booking_id = %s
                ORDER BY stop_number
            """, (delivery_id,))
            updated_delivery['stops'] = cursor.fetchall()
            
            # Convert datetime objects to strings
            for key, value in updated_delivery.items():
                if isinstance(value, datetime):
                    updated_delivery[key] = value.isoformat()
            for stop in updated_delivery['stops']:
                for key, value in stop.items():
                    if isinstance(value, datetime):
                        stop[key] = value.isoformat()
            
            # Send tracking update email when delivery is accepted
            sender_email = updated_delivery.get('sender_email')
            if sender_email:
                try:
                    send_tracking_update(
                        to_email=sender_email,
                        tracking_id=delivery_id,
                        sender_name=updated_delivery.get('sender_name', ''),
                        status='accepted',
                        partner_name=partner_name
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Failed to send tracking update email: {str(e)}")
            
            return jsonify({'success': True, 'delivery': updated_delivery})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/partner/update-status', methods=['POST'])
def update_delivery_status():
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.json
        delivery_id = data.get('delivery_id')
        new_status = data.get('status')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if delivery belongs to this partner
            cursor.execute("""
                SELECT id, partner_id FROM deliveries WHERE id = %s
            """, (delivery_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404
            
            if delivery['partner_id'] != partner_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Update delivery status
            if new_status == 'delivered':
                # Check if this is a multi-stop delivery
                cursor.execute("SELECT COUNT(*) as total FROM delivery_stops WHERE booking_id = %s", (delivery_id,))
                stops_count = cursor.fetchone()['total']
                
                if stops_count > 1:
                    # For multi-stop, check if all stops are delivered
                    cursor.execute("""
                        SELECT COUNT(*) as total, SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered
                        FROM delivery_stops WHERE booking_id = %s
                    """, (delivery_id,))
                    stop_stats = cursor.fetchone()
                    
                    # Only mark as delivered if all stops are delivered
                    if stop_stats['delivered'] == stop_stats['total']:
                        cursor.execute("""
                            UPDATE deliveries 
                            SET status = %s, updated_at = NOW(), delivered_at = NOW(), payment_status = 'pending'
                            WHERE id = %s
                        """, (new_status, delivery_id))
                    else:
                        return jsonify({'success': False, 'message': 'All stops must be delivered first'}), 400
                else:
                    # Single stop delivery - mark as delivered and set payment pending
                    cursor.execute("""
                        UPDATE deliveries 
                        SET status = %s, updated_at = NOW(), delivered_at = NOW(), payment_status = 'pending'
                        WHERE id = %s
                    """, (new_status, delivery_id))
            else:
                cursor.execute("""
                    UPDATE deliveries 
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s
                """, (new_status, delivery_id))
            
            conn.commit()
            
            # Get updated delivery with sender_email
            cursor.execute("""
                SELECT id, sender_name, sender_address, sender_email, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id,
                       created_at, accepted_at, updated_at, delivered_at,
                       payment_status, payment_method, total_amount
                FROM deliveries WHERE id = %s
            """, (delivery_id,))
            updated_delivery = cursor.fetchone()
            
            # Get partner name if partner_id exists
            partner_name = None
            if updated_delivery.get('partner_id'):
                cursor.execute("""
                    SELECT first_name, last_name FROM partners WHERE id = %s
                """, (updated_delivery['partner_id'],))
                partner = cursor.fetchone()
                if partner:
                    partner_name = f"{partner['first_name']} {partner['last_name']}"
            
            # Convert datetime objects to strings
            for key, value in updated_delivery.items():
                if isinstance(value, datetime):
                    updated_delivery[key] = value.isoformat()
            
            # Send tracking update email if sender email is provided
            sender_email = updated_delivery.get('sender_email')
            if sender_email:
                try:
                    send_tracking_update(
                        to_email=sender_email,
                        tracking_id=delivery_id,
                        sender_name=updated_delivery.get('sender_name', ''),
                        status=new_status,
                        partner_name=partner_name
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Failed to send tracking update email: {str(e)}")
            
            return jsonify({'success': True, 'delivery': updated_delivery})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API endpoint to mark a specific stop as delivered
@app.route('/api/partner/deliver-stop', methods=['POST'])
def deliver_stop():
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.json
        delivery_id = data.get('delivery_id')
        stop_number = data.get('stop_number')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Verify delivery belongs to partner
            cursor.execute("""
                SELECT id, partner_id FROM deliveries WHERE id = %s
            """, (delivery_id,))
            delivery = cursor.fetchone()
            
            if not delivery or delivery['partner_id'] != partner_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Update stop status
            cursor.execute("""
                UPDATE delivery_stops 
                SET status = 'delivered', delivered_at = NOW()
                WHERE booking_id = %s AND stop_number = %s
            """, (delivery_id, stop_number))
            
            # Check if all stops are delivered
            cursor.execute("""
                SELECT COUNT(*) as total, SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered
                FROM delivery_stops WHERE booking_id = %s
            """, (delivery_id,))
            stop_stats = cursor.fetchone()
            
            # If all stops delivered, update main delivery status and set payment pending
            if stop_stats['delivered'] == stop_stats['total']:
                cursor.execute("""
                    UPDATE deliveries 
                    SET status = 'delivered', delivered_at = NOW(), payment_status = 'pending'
                    WHERE id = %s
                """, (delivery_id,))
            
            conn.commit()
            
            # Return delivery_id so frontend can redirect to payment if all stops delivered
            all_delivered = stop_stats['delivered'] == stop_stats['total']
            return jsonify({
                'success': True, 
                'message': 'Stop marked as delivered',
                'all_delivered': all_delivered,
                'delivery_id': delivery_id
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API endpoint to get delivery details by tracking ID
@app.route('/api/deliveries/track/<tracking_id>', methods=['GET'])
def track_delivery(tracking_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get delivery
            cursor.execute("""
                SELECT id, sender_name, sender_address, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id, total_stops,
                       created_at, accepted_at, updated_at, delivered_at,
                       total_amount, payment_status, payment_method
                FROM deliveries WHERE id = %s
            """, (tracking_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return jsonify({'success': False, 'message': 'Tracking number not found'}), 404
            
            # Get stops
            cursor.execute("""
                SELECT stop_number, drop_address, receiver_name, receiver_phone, status, delivered_at
                FROM delivery_stops
                WHERE booking_id = %s
                ORDER BY stop_number
            """, (tracking_id,))
            stops = cursor.fetchall()
            
            # Convert datetime objects to strings
            for key, value in delivery.items():
                if isinstance(value, datetime):
                    delivery[key] = value.isoformat()
            for stop in stops:
                for key, value in stop.items():
                    if isinstance(value, datetime):
                        stop[key] = value.isoformat()
            
            delivery['stops'] = stops
            
            return jsonify({'success': True, 'delivery': delivery})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/deliveries/create', methods=['POST'])
def create_delivery():
    try:
        data = request.json
        stops = data.get('stops', [])
        total_stops = len(stops)
        
        if total_stops == 0:
            return jsonify({'success': False, 'message': 'At least one stop is required'}), 400
        
        # Use first stop as primary receiver (for backward compatibility)
        first_stop = stops[0]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate delivery ID
            cursor.execute("SELECT COUNT(*) FROM deliveries")
            count = cursor.fetchone()[0]
            delivery_id = f"QP{count + 1:09d}"
            
            # Calculate total amount
            pickup_address = data.get('senderAddress')
            weight = float(data.get('parcelWeight', 0))
            total_distance = calculate_total_distance(pickup_address, stops)
            price_breakdown = calculate_price(total_distance, weight, total_stops)
            total_amount = price_breakdown['total']
            
            # Validate sender email if provided
            sender_email = data.get('senderEmail', '').strip()
            if sender_email:
                from validation import validate_email
                is_valid, error = validate_email(sender_email)
                if not is_valid:
                    return jsonify({'success': False, 'message': error}), 400
            
            # Check if total_amount column exists
            cursor.execute("SHOW COLUMNS FROM deliveries LIKE 'total_amount'")
            has_total_amount = cursor.fetchone() is not None
            
            # Check if sender_email column exists
            cursor.execute("SHOW COLUMNS FROM deliveries LIKE 'sender_email'")
            has_sender_email = cursor.fetchone() is not None
            
            # Insert new delivery
            if has_total_amount and has_sender_email:
                cursor.execute("""
                    INSERT INTO deliveries (id, sender_name, sender_address, sender_email, receiver_name, 
                                         receiver_address, receiver_phone, parcel_type, weight, status, total_stops, total_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available', %s, %s)
                """, (
                    delivery_id,
                    data.get('senderName'),
                    data.get('senderAddress'),
                    sender_email if sender_email else None,
                    first_stop.get('receiver_name'),
                    first_stop.get('drop_address'),
                    first_stop.get('receiver_phone'),
                    data.get('parcelType'),
                    weight,
                    total_stops,
                    total_amount
                ))
            elif has_total_amount:
                # sender_email column doesn't exist yet
                cursor.execute("""
                    INSERT INTO deliveries (id, sender_name, sender_address, receiver_name, 
                                         receiver_address, receiver_phone, parcel_type, weight, status, total_stops, total_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'available', %s, %s)
                """, (
                    delivery_id,
                    data.get('senderName'),
                    data.get('senderAddress'),
                    first_stop.get('receiver_name'),
                    first_stop.get('drop_address'),
                    first_stop.get('receiver_phone'),
                    data.get('parcelType'),
                    weight,
                    total_stops,
                    total_amount
                ))
            elif has_sender_email:
                # total_amount column doesn't exist yet
                cursor.execute("""
                    INSERT INTO deliveries (id, sender_name, sender_address, sender_email, receiver_name, 
                                         receiver_address, receiver_phone, parcel_type, weight, status, total_stops)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'available', %s)
                """, (
                    delivery_id,
                    data.get('senderName'),
                    data.get('senderAddress'),
                    sender_email if sender_email else None,
                    first_stop.get('receiver_name'),
                    first_stop.get('drop_address'),
                    first_stop.get('receiver_phone'),
                    data.get('parcelType'),
                    weight,
                    total_stops
                ))
                # Try to add total_amount after insert
                try:
                    cursor.execute("UPDATE deliveries SET total_amount = %s WHERE id = %s", (total_amount, delivery_id))
                except:
                    pass  # Column doesn't exist yet, will be added by migration
            else:
                # Fallback: insert without total_amount and sender_email (migration will add them later)
                cursor.execute("""
                    INSERT INTO deliveries (id, sender_name, sender_address, receiver_name, 
                                         receiver_address, receiver_phone, parcel_type, weight, status, total_stops)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'available', %s)
                """, (
                    delivery_id,
                    data.get('senderName'),
                    data.get('senderAddress'),
                    first_stop.get('receiver_name'),
                    first_stop.get('drop_address'),
                    first_stop.get('receiver_phone'),
                    data.get('parcelType'),
                    weight,
                    total_stops
                ))
                # Try to add total_amount and sender_email after insert
                try:
                    cursor.execute("UPDATE deliveries SET total_amount = %s WHERE id = %s", (total_amount, delivery_id))
                except:
                    pass  # Column doesn't exist yet, will be added by migration
                try:
                    if sender_email:
                        cursor.execute("UPDATE deliveries SET sender_email = %s WHERE id = %s", (sender_email, delivery_id))
                except:
                    pass  # Column doesn't exist yet, will be added by migration
            
            # Insert all stops
            for stop in stops:
                cursor.execute("""
                    INSERT INTO delivery_stops (booking_id, stop_number, drop_address, receiver_name, receiver_phone, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                """, (
                    delivery_id,
                    stop.get('stop_number'),
                    stop.get('drop_address'),
                    stop.get('receiver_name'),
                    stop.get('receiver_phone')
                ))
            
            conn.commit()
            
            # Get created delivery
            cursor_dict = conn.cursor(dictionary=True)
            cursor_dict.execute("""
                SELECT id, sender_name, sender_address, receiver_name, receiver_address,
                       receiver_phone, parcel_type, weight, status, partner_id, total_stops,
                       created_at, accepted_at, updated_at, delivered_at
                FROM deliveries WHERE id = %s
            """, (delivery_id,))
            delivery_dict = cursor_dict.fetchone()
            cursor_dict.close()
            
            # Convert datetime objects to strings
            if delivery_dict:
                for key, value in delivery_dict.items():
                    if isinstance(value, datetime):
                        delivery_dict[key] = value.isoformat()
            
            # Send confirmation email if sender email is provided
            if sender_email:
                try:
                    send_confirmation_email(
                        to_email=sender_email,
                        tracking_id=delivery_id,
                        sender_name=data.get('senderName', ''),
                        receiver_name=first_stop.get('receiver_name', ''),
                        sender_address=data.get('senderAddress', ''),
                        receiver_address=first_stop.get('drop_address', ''),
                        parcel_type=data.get('parcelType', ''),
                        weight=weight,
                        total_stops=total_stops,
                        total_amount=total_amount
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Failed to send confirmation email: {str(e)}")
            
            return jsonify({
                'success': True, 
                'delivery_id': delivery_id, 
                'delivery': delivery_dict,
                'total_stops': total_stops
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Pricing Configuration
BASE_FARE = 30
PRICE_PER_KM = 8
PRICE_PER_KG = 5
EXTRA_STOP_CHARGE = 15

# Google Distance Matrix API Key (set in environment variable or config)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

def calculate_distance(origin, destination, api_key=None):
    """
    Calculate distance between two addresses using Google Distance Matrix API
    Returns distance in kilometers, or None if API call fails
    """
    if not api_key:
        # Fallback: Return estimated distance (for demo purposes)
        # In production, you should always use the API
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': origin,
            'destinations': destination,
            'key': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            distance_text = data['rows'][0]['elements'][0]['distance']['text']
            distance_value = data['rows'][0]['elements'][0]['distance']['value'] / 1000  # Convert to km
            return round(distance_value, 2)
        else:
            return None
    except Exception as e:
        print(f"Distance calculation error: {e}")
        return None

def calculate_total_distance(pickup_address, stops):
    """
    Calculate total distance for multi-stop delivery
    Returns total distance in kilometers
    """
    total_distance = 0
    
    if not stops or len(stops) == 0:
        return 0
    
    # Calculate pickup to first stop
    if GOOGLE_API_KEY:
        distance = calculate_distance(pickup_address, stops[0]['drop_address'], GOOGLE_API_KEY)
        if distance:
            total_distance += distance
        else:
            # Fallback: estimate 5km per segment
            total_distance += 5
    else:
        # Fallback: estimate 5km per segment
        total_distance += 5
    
    # Calculate distances between stops
    for i in range(len(stops) - 1):
        if GOOGLE_API_KEY:
            distance = calculate_distance(
                stops[i]['drop_address'], 
                stops[i + 1]['drop_address'], 
                GOOGLE_API_KEY
            )
            if distance:
                total_distance += distance
            else:
                total_distance += 5
        else:
            total_distance += 5
    
    return round(total_distance, 2)

def calculate_price(distance, weight, num_stops):
    """
    Calculate delivery price based on:
    - Base Fare: ₹30
    - Price per km: ₹8
    - Price per kg: ₹5
    - Extra stop charge: ₹15 per stop (after first stop)
    """
    base_fare = BASE_FARE
    distance_cost = distance * PRICE_PER_KM
    weight_cost = weight * PRICE_PER_KG
    extra_stops = max(0, num_stops - 1)  # First stop is free
    extra_stop_cost = extra_stops * EXTRA_STOP_CHARGE
    
    total = base_fare + distance_cost + weight_cost + extra_stop_cost
    
    return {
        'base_fare': base_fare,
        'distance': round(distance, 2),
        'distance_cost': round(distance_cost, 2),
        'weight': round(weight, 2),
        'weight_cost': round(weight_cost, 2),
        'num_stops': num_stops,
        'extra_stops': extra_stops,
        'extra_stop_cost': round(extra_stop_cost, 2),
        'total': round(total, 2)
    }

@app.route('/api/calculate-price', methods=['POST'])
def calculate_price_endpoint():
    try:
        data = request.json
        pickup_address = data.get('pickup_address', '')
        stops = data.get('stops', [])
        weight = float(data.get('weight', 0))
        
        if not pickup_address or len(stops) == 0:
            return jsonify({
                'success': False,
                'message': 'Pickup address and at least one stop are required'
            }), 400
        
        # Calculate total distance
        total_distance = calculate_total_distance(pickup_address, stops)
        
        # Calculate price
        price_breakdown = calculate_price(total_distance, weight, len(stops))
        
        return jsonify({
            'success': True,
            'price_breakdown': price_breakdown
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Admin API Routes
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Demo credentials: admin@boxy.com / admin123
        if email == 'admin@boxy.com' and password == 'admin123':
            session['admin_logged_in'] = True
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Total parcels
            cursor.execute("SELECT COUNT(*) as total FROM deliveries")
            total_parcels = cursor.fetchone()['total']
            
            # Delivered today
            cursor.execute("""
                SELECT COUNT(*) as delivered_today 
                FROM deliveries 
                WHERE DATE(delivered_at) = CURDATE() AND status = 'delivered'
            """)
            delivered_today = cursor.fetchone()['delivered_today']
            
            # In transit (accepted, picked, on_the_way)
            cursor.execute("""
                SELECT COUNT(*) as in_transit 
                FROM deliveries 
                WHERE status IN ('accepted', 'picked', 'on_the_way')
            """)
            in_transit = cursor.fetchone()['in_transit']
            
            # Pending (available)
            cursor.execute("""
                SELECT COUNT(*) as pending 
                FROM deliveries 
                WHERE status = 'available'
            """)
            pending = cursor.fetchone()['pending']
            
            # Total partners
            cursor.execute("SELECT COUNT(*) as total_partners FROM partners")
            total_partners = cursor.fetchone()['total_partners']
            
            # Active partners (online)
            cursor.execute("""
                SELECT COUNT(*) as active_partners 
                FROM partners 
                WHERE status = 'online'
            """)
            active_partners = cursor.fetchone()['active_partners']
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_parcels': total_parcels,
                    'delivered_today': delivered_today,
                    'in_transit': in_transit,
                    'pending': pending,
                    'total_partners': total_partners,
                    'active_partners': active_partners
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/deliveries', methods=['GET'])
def admin_deliveries():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        limit = request.args.get('limit', 20, type=int)
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT d.id, d.sender_name, d.receiver_name, d.status, 
                       d.created_at, d.delivered_at, d.total_stops,
                       p.first_name, p.last_name
                FROM deliveries d
                LEFT JOIN partners p ON d.partner_id = p.id
                ORDER BY d.created_at DESC
                LIMIT %s
            """, (limit,))
            
            deliveries = cursor.fetchall()
            
            # Format dates and add partner name
            for delivery in deliveries:
                if delivery['first_name'] and delivery['last_name']:
                    delivery['partner_name'] = f"{delivery['first_name']} {delivery['last_name']}"
                else:
                    delivery['partner_name'] = 'Unassigned'
                
                if delivery['created_at']:
                    delivery['created_at'] = delivery['created_at'].strftime('%b %d, %Y')
                if delivery['delivered_at']:
                    delivery['delivered_at'] = delivery['delivered_at'].strftime('%b %d, %Y')
            
            return jsonify({
                'success': True,
                'deliveries': deliveries
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Payment Routes
@app.route('/payment/<tracking_id>')
def payment_page(tracking_id):
    """Show payment page for a delivery"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, sender_name, sender_address, receiver_name, receiver_address,
                       total_amount, payment_status, payment_method, status, weight, 
                       parcel_type, total_stops
                FROM deliveries WHERE id = %s
            """, (tracking_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return render_template('error.html', message='Delivery not found'), 404
            
            # Only allow payment if delivery is delivered and payment is pending
            if delivery['status'] != 'delivered':
                return render_template('error.html', message='Delivery not yet completed'), 400
            
            if delivery['payment_status'] == 'paid':
                return render_template('payment_success.html', delivery=delivery)
            
            # If total_amount is NULL or 0, calculate it
            if not delivery['total_amount'] or delivery['total_amount'] == 0:
                # Get stops to calculate distance
                cursor.execute("""
                    SELECT drop_address, stop_number
                    FROM delivery_stops
                    WHERE booking_id = %s
                    ORDER BY stop_number
                """, (tracking_id,))
                stops_data = cursor.fetchall()
                
                stops = [{'drop_address': stop['drop_address']} for stop in stops_data]
                weight = float(delivery.get('weight', 0) or 0)
                total_stops = delivery.get('total_stops', 1) or len(stops) or 1
                
                # Calculate total amount
                pickup_address = delivery.get('sender_address', '')
                total_distance = calculate_total_distance(pickup_address, stops)
                price_breakdown = calculate_price(total_distance, weight, total_stops)
                calculated_amount = price_breakdown['total']
                
                # Update the delivery with calculated amount
                cursor.execute("""
                    UPDATE deliveries 
                    SET total_amount = %s 
                    WHERE id = %s
                """, (calculated_amount, tracking_id))
                conn.commit()
                
                delivery['total_amount'] = calculated_amount
            
            return render_template('payment.html', delivery=delivery)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@app.route('/api/payment/create-order', methods=['POST'])
def create_razorpay_order():
    """Create a Razorpay order for payment"""
    try:
        data = request.json
        tracking_id = data.get('tracking_id')
        amount = float(data.get('amount', 0))
        
        # Validate amount - if 0 or invalid, try to get from database
        if amount <= 0:
            with get_db_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT total_amount FROM deliveries WHERE id = %s", (tracking_id,))
                delivery = cursor.fetchone()
                
                if delivery and delivery.get('total_amount') and float(delivery['total_amount']) > 0:
                    amount = float(delivery['total_amount'])
                else:
                    return jsonify({
                        'success': False, 
                        'message': 'Invalid amount. Amount must be greater than ₹0.'
                    }), 400
        
        # Razorpay minimum amount is 1 rupee (100 paise)
        if amount < 1:
            return jsonify({
                'success': False, 
                'message': 'Minimum payment amount is ₹1.'
            }), 400
        
        # Create Razorpay order
        order_data = {
            'amount': int(amount * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': tracking_id,
            'notes': {
                'tracking_id': tracking_id,
                'description': f'Payment for Delivery {tracking_id}'
            }
        }
        
        # Make API request to Razorpay
        response = requests.post(
            'https://api.razorpay.com/v1/orders',
            json=order_data,
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            order = response.json()
            return jsonify({
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'key_id': RAZORPAY_KEY_ID
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to create order: {response.text}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment/razorpay-success', methods=['POST'])
def razorpay_success():
    """Handle Razorpay payment success with signature verification"""
    try:
        data = request.json
        tracking_id = data.get('tracking_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Verify signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return jsonify({
                'success': False,
                'message': 'Payment signature verification failed'
            }), 400
        
        # Verify payment with Razorpay API
        try:
            payment_response = requests.get(
                f'https://api.razorpay.com/v1/payments/{razorpay_payment_id}',
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
            )
            
            if payment_response.status_code != 200:
                return jsonify({
                    'success': False,
                    'message': 'Payment verification failed'
                }), 400
            
            payment_data = payment_response.json()
            
            # Check if payment is successful
            if payment_data.get('status') != 'captured' and payment_data.get('status') != 'authorized':
                return jsonify({
                    'success': False,
                    'message': f"Payment status: {payment_data.get('status')}"
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Payment verification error: {str(e)}'
            }), 500
        
        # Update delivery payment status
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get delivery info before updating
            cursor.execute("""
                SELECT sender_name, sender_email, total_amount
                FROM deliveries WHERE id = %s
            """, (tracking_id,))
            delivery_info = cursor.fetchone()
            
            # Update payment status
            cursor.execute("""
                UPDATE deliveries 
                SET payment_status = 'paid', 
                    payment_method = 'online',
                    status = 'completed'
                WHERE id = %s AND payment_status = 'pending'
            """, (tracking_id,))
            
            if cursor.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': 'Payment already processed or delivery not found'
                }), 400
            
            conn.commit()
            
            # Send payment receipt email if sender email is provided
            if delivery_info and delivery_info.get('sender_email'):
                try:
                    send_payment_receipt(
                        to_email=delivery_info['sender_email'],
                        tracking_id=tracking_id,
                        sender_name=delivery_info.get('sender_name', ''),
                        total_amount=float(delivery_info.get('total_amount', 0)),
                        payment_method='online',
                        payment_id=razorpay_payment_id
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Failed to send payment receipt email: {str(e)}")
            
            return jsonify({
                'success': True,
                'message': 'Payment successful',
                'payment_id': razorpay_payment_id
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/payment-success/<tracking_id>')
def payment_success_page(tracking_id):
    """Show payment success page"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, sender_name, receiver_name, total_amount, payment_status, payment_method, status
                FROM deliveries WHERE id = %s
            """, (tracking_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return render_template('error.html', message='Delivery not found'), 404
            
            # Only show success if payment is actually paid
            if delivery['payment_status'] != 'paid':
                return render_template('error.html', message='Payment not completed'), 400
            
            return render_template('payment_success.html', delivery=delivery)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@app.route('/api/payment/cash-confirm/<booking_id>', methods=['POST'])
def cash_payment_confirm(booking_id):
    """Partner confirms cash payment received"""
    try:
        partner_id = session.get('partner_id')
        if not partner_id:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Verify delivery belongs to partner and is COD
            cursor.execute("""
                SELECT id, partner_id, payment_method, payment_status 
                FROM deliveries 
                WHERE id = %s
            """, (booking_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404
            
            if delivery['partner_id'] != partner_id:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            if delivery['payment_method'] != 'cash':
                return jsonify({'success': False, 'message': 'Not a cash payment'}), 400
            
            # Get delivery info before updating
            cursor.execute("""
                SELECT sender_name, sender_email, total_amount
                FROM deliveries WHERE id = %s
            """, (booking_id,))
            delivery_info = cursor.fetchone()
            
            # Update payment status (use regular cursor for UPDATE)
            cursor.execute("""
                UPDATE deliveries 
                SET payment_status = 'paid',
                    status = 'completed'
                WHERE id = %s
            """, (booking_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'Failed to update payment status'}), 400
            
            conn.commit()
            
            # Send payment receipt email if sender email is provided
            if delivery_info and delivery_info.get('sender_email'):
                try:
                    send_payment_receipt(
                        to_email=delivery_info['sender_email'],
                        tracking_id=booking_id,
                        sender_name=delivery_info.get('sender_name', ''),
                        total_amount=float(delivery_info.get('total_amount', 0)),
                        payment_method='cash',
                        payment_id=None
                    )
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Failed to send payment receipt email: {str(e)}")
            
            return jsonify({'success': True, 'message': 'Cash payment confirmed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment/status/<tracking_id>', methods=['GET'])
def payment_status(tracking_id):
    """Get payment status for a delivery"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT payment_status, payment_method, total_amount, status
                FROM deliveries WHERE id = %s
            """, (tracking_id,))
            delivery = cursor.fetchone()
            
            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404
            
            return jsonify({
                'success': True,
                'payment_status': delivery['payment_status'],
                'payment_method': delivery['payment_method'],
                'total_amount': float(delivery['total_amount']) if delivery['total_amount'] else 0,
                'status': delivery['status']
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/payment/select-cod/<tracking_id>', methods=['POST'])
def select_cod(tracking_id):
    """Customer selects Cash on Delivery"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE deliveries 
                SET payment_method = 'cash', 
                    payment_status = 'pending_cash'
                WHERE id = %s AND payment_status = 'pending'
            """, (tracking_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'Payment already processed or delivery not found'}), 400
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Cash on Delivery selected. Payment will be collected on delivery.'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/partners', methods=['GET'])
def admin_partners():
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, first_name, last_name, email, phone, vehicle_type, 
                       status, approved, created_at
                FROM partners
                ORDER BY created_at DESC
            """)
            
            partners = cursor.fetchall()
            
            for partner in partners:
                partner['name'] = f"{partner['first_name']} {partner['last_name']}"
                if partner['created_at']:
                    partner['created_at'] = partner['created_at'].strftime('%b %d, %Y')
            
            return jsonify({
                'success': True,
                'partners': partners
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/export/csv', methods=['GET'])
def export_admin_data_csv():
    """Export deliveries data as CSV"""
    try:
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Get all deliveries data
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT d.id, d.sender_name, d.sender_address, d.receiver_name, 
                       d.receiver_address, d.receiver_phone, d.parcel_type, 
                       d.weight, d.status, d.created_at, d.delivered_at, 
                       d.total_stops, d.total_amount, d.payment_status,
                       p.first_name, p.last_name
                FROM deliveries d
                LEFT JOIN partners p ON d.partner_id = p.id
                ORDER BY d.created_at DESC
            """)
            
            deliveries = cursor.fetchall()
            
            # Format data
            for delivery in deliveries:
                if delivery['first_name'] and delivery['last_name']:
                    delivery['partner_name'] = f"{delivery['first_name']} {delivery['last_name']}"
                else:
                    delivery['partner_name'] = 'Unassigned'
                
                if delivery['created_at']:
                    delivery['created_at'] = delivery['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if delivery['delivered_at']:
                    delivery['delivered_at'] = delivery['delivered_at'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    delivery['delivered_at'] = 'N/A'
                
                if not delivery['total_amount']:
                    delivery['total_amount'] = 0
        
        return generate_csv(deliveries)
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def generate_csv(deliveries):
    """Generate CSV file from deliveries data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Tracking ID', 'Sender Name', 'Sender Address', 'Receiver Name',
        'Receiver Address', 'Receiver Phone', 'Parcel Type', 'Weight (kg)',
        'Status', 'Partner', 'Total Stops', 'Total Amount', 'Payment Status',
        'Created At', 'Delivered At'
    ])
    
    # Write data
    for delivery in deliveries:
        writer.writerow([
            delivery['id'],
            delivery['sender_name'] or 'N/A',
            delivery['sender_address'] or 'N/A',
            delivery['receiver_name'] or 'N/A',
            delivery['receiver_address'] or 'N/A',
            delivery['receiver_phone'] or 'N/A',
            delivery['parcel_type'] or 'N/A',
            delivery['weight'] or 0,
            delivery['status'] or 'N/A',
            delivery['partner_name'],
            delivery['total_stops'] or 1,
            delivery['total_amount'] or 0,
            delivery['payment_status'] or 'N/A',
            delivery['created_at'] or 'N/A',
            delivery['delivered_at']
        ])
    
    # Create response with date and time in filename
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response.headers['Content-Disposition'] = f'attachment; filename=deliveries_export_{timestamp}.csv'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
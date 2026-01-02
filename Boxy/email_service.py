"""
Email service module for sending automated emails via SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template_string
from config import SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT, SMTP_USE_TLS
import logging

logger = logging.getLogger(__name__)

def send_email(to_email, subject, html_body, text_body=None):
    """
    Send an email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Skip if SMTP not configured
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️ WARNING: SMTP not configured. Email not sent.")
        print(f"   SMTP_EMAIL: {'SET' if SMTP_EMAIL else 'NOT SET'}")
        print(f"   SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
        logger.warning("SMTP not configured. Email not sent.")
        return False
    
    # Skip if recipient email is empty
    if not to_email or not to_email.strip():
        logger.warning(f"Recipient email is empty. Email not sent.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Connect to SMTP server and send
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_confirmation_email(to_email, tracking_id, sender_name, receiver_name, 
                           sender_address, receiver_address, parcel_type, weight, 
                           total_stops, total_amount):
    """
    Send booking confirmation email
    
    Args:
        to_email: Recipient email address
        tracking_id: Delivery tracking ID
        sender_name: Sender's name
        receiver_name: Receiver's name
        sender_address: Pickup address
        receiver_address: Delivery address
        parcel_type: Type of parcel
        weight: Parcel weight in kg
        total_stops: Total number of stops
        total_amount: Total delivery amount
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = f"Booking Confirmation - Tracking ID: {tracking_id}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
            .tracking-id {{ font-size: 24px; font-weight: bold; color: #007bff; margin: 20px 0; }}
            .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            .label {{ font-weight: bold; color: #555; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Booking Confirmed!</h1>
            </div>
            <div class="content">
                <p>Dear {sender_name},</p>
                <p>Your parcel booking has been confirmed successfully. Here are your booking details:</p>
                
                <div class="tracking-id">Tracking ID: {tracking_id}</div>
                
                <div class="info-box">
                    <p><span class="label">Sender:</span> {sender_name}</p>
                    <p><span class="label">Pickup Address:</span> {sender_address}</p>
                </div>
                
                <div class="info-box">
                    <p><span class="label">Receiver:</span> {receiver_name}</p>
                    <p><span class="label">Delivery Address:</span> {receiver_address}</p>
                </div>
                
                <div class="info-box">
                    <p><span class="label">Parcel Type:</span> {parcel_type}</p>
                    <p><span class="label">Weight:</span> {weight} kg</p>
                    <p><span class="label">Total Stops:</span> {total_stops}</p>
                    <p><span class="label">Estimated Amount:</span> ₹{total_amount:.2f}</p>
                </div>
                
                <p style="margin-top: 20px;">You can track your parcel using the tracking ID above on our website.</p>
                
                <div class="footer">
                    <p>Thank you for choosing Boxy!</p>
                    <p>If you have any questions, please contact us at support@boxy.com</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Booking Confirmation - Tracking ID: {tracking_id}
    
    Dear {sender_name},
    
    Your parcel booking has been confirmed successfully.
    
    Tracking ID: {tracking_id}
    
    Sender: {sender_name}
    Pickup Address: {sender_address}
    
    Receiver: {receiver_name}
    Delivery Address: {receiver_address}
    
    Parcel Type: {parcel_type}
    Weight: {weight} kg
    Total Stops: {total_stops}
    Estimated Amount: ₹{total_amount:.2f}
    
    You can track your parcel using the tracking ID above on our website.
    
    Thank you for choosing Boxy!
    """
    
    return send_email(to_email, subject, html_body, text_body)

def send_tracking_update(to_email, tracking_id, sender_name, status, partner_name=None):
    """
    Send tracking status update email
    
    Args:
        to_email: Recipient email address
        tracking_id: Delivery tracking ID
        sender_name: Sender's name
        status: Current delivery status
        partner_name: Partner name (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    status_messages = {
        'available': 'Your parcel is available and waiting to be assigned to a delivery partner.',
        'accepted': 'Your parcel has been accepted by a delivery partner and will be picked up soon.',
        'picked': 'Your parcel has been picked up and is on its way.',
        'on_the_way': 'Your parcel is on the way to the delivery address.',
        'delivered': 'Your parcel has been delivered successfully!',
        'completed': 'Your delivery has been completed successfully!'
    }
    
    status_display = {
        'available': 'Available',
        'accepted': 'Accepted',
        'picked': 'Picked Up',
        'on_the_way': 'On The Way',
        'delivered': 'Delivered',
        'completed': 'Completed'
    }
    
    message = status_messages.get(status, 'Your parcel status has been updated.')
    display_status = status_display.get(status, status.title())
    
    subject = f"Tracking Update - {tracking_id}: {display_status}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
            .status-badge {{ display: inline-block; background-color: #28a745; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; margin: 20px 0; }}
            .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }}
            .tracking-id {{ font-size: 20px; font-weight: bold; color: #007bff; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Tracking Update</h1>
            </div>
            <div class="content">
                <p>Dear {sender_name},</p>
                <p>Your parcel status has been updated:</p>
                
                <div class="tracking-id">Tracking ID: {tracking_id}</div>
                
                <div style="text-align: center;">
                    <div class="status-badge">{display_status}</div>
                </div>
                
                <div class="info-box">
                    <p>{message}</p>
                    {f'<p><strong>Delivery Partner:</strong> {partner_name}</p>' if partner_name else ''}
                </div>
                
                <p style="margin-top: 20px;">You can continue tracking your parcel on our website using the tracking ID above.</p>
                
                <div class="footer">
                    <p>Thank you for choosing Boxy!</p>
                    <p>If you have any questions, please contact us at support@boxy.com</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Tracking Update - {tracking_id}: {display_status}
    
    Dear {sender_name},
    
    Your parcel status has been updated.
    
    Tracking ID: {tracking_id}
    Status: {display_status}
    
    {message}
    {f'Delivery Partner: {partner_name}' if partner_name else ''}
    
    You can continue tracking your parcel on our website using the tracking ID above.
    
    Thank you for choosing Boxy!
    """
    
    return send_email(to_email, subject, html_body, text_body)

def send_payment_receipt(to_email, tracking_id, sender_name, total_amount, 
                        payment_method, payment_id=None):
    """
    Send payment receipt email
    
    Args:
        to_email: Recipient email address
        tracking_id: Delivery tracking ID
        sender_name: Sender's name
        total_amount: Payment amount
        payment_method: Payment method (online/cash)
        payment_id: Payment transaction ID (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = f"Payment Receipt - {tracking_id}"
    
    payment_method_display = 'Online Payment' if payment_method == 'online' else 'Cash on Delivery'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f8f9fa; padding: 20px; border-radius: 0 0 5px 5px; }}
            .success-badge {{ display: inline-block; background-color: #28a745; color: white; padding: 10px 20px; border-radius: 20px; font-weight: bold; margin: 20px 0; }}
            .info-box {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }}
            .amount {{ font-size: 28px; font-weight: bold; color: #28a745; text-align: center; margin: 20px 0; }}
            .tracking-id {{ font-size: 20px; font-weight: bold; color: #007bff; }}
            .label {{ font-weight: bold; color: #555; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Payment Successful!</h1>
            </div>
            <div class="content">
                <p>Dear {sender_name},</p>
                <p>Your payment has been processed successfully. Here is your payment receipt:</p>
                
                <div class="tracking-id">Tracking ID: {tracking_id}</div>
                
                <div style="text-align: center;">
                    <div class="success-badge">Payment Confirmed</div>
                </div>
                
                <div class="amount">₹{total_amount:.2f}</div>
                
                <div class="info-box">
                    <p><span class="label">Payment Method:</span> {payment_method_display}</p>
                    <p><span class="label">Amount Paid:</span> ₹{total_amount:.2f}</p>
                    {f'<p><span class="label">Transaction ID:</span> {payment_id}</p>' if payment_id else ''}
                    <p><span class="label">Status:</span> Paid</p>
                </div>
                
                <p style="margin-top: 20px;">This receipt confirms that your payment for delivery {tracking_id} has been successfully processed.</p>
                
                <div class="footer">
                    <p>Thank you for choosing Boxy!</p>
                    <p>If you have any questions, please contact us at support@boxy.com</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Payment Receipt - {tracking_id}
    
    Dear {sender_name},
    
    Your payment has been processed successfully.
    
    Tracking ID: {tracking_id}
    Payment Method: {payment_method_display}
    Amount Paid: ₹{total_amount:.2f}
    {f'Transaction ID: {payment_id}' if payment_id else ''}
    Status: Paid
    
    This receipt confirms that your payment for delivery {tracking_id} has been successfully processed.
    
    Thank you for choosing Boxy!
    """
    
    return send_email(to_email, subject, html_body, text_body)


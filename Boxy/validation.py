"""
Validation module for Boxy application
Clean validation functions without regex
"""

def validate_email(email):
    """
    Validate email address format
    Returns: (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip()
    
    if len(email) < 5:
        return False, "Email is too short"
    
    if len(email) > 100:
        return False, "Email is too long"
    
    # Check for @ symbol
    if '@' not in email:
        return False, "Email must contain @ symbol"
    
    parts = email.split('@')
    if len(parts) != 2:
        return False, "Email must have exactly one @ symbol"
    
    local_part, domain = parts[0], parts[1]
    
    # Validate local part (before @)
    if len(local_part) == 0:
        return False, "Email local part cannot be empty"
    
    if len(local_part) > 64:
        return False, "Email local part is too long"
    
    # Validate domain (after @)
    if len(domain) == 0:
        return False, "Email domain cannot be empty"
    
    if '.' not in domain:
        return False, "Email domain must contain a dot"
    
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        return False, "Email domain must have at least one dot"
    
    # Check TLD (last part after last dot)
    tld = domain_parts[-1]
    if len(tld) < 2:
        return False, "Email domain extension must be at least 2 characters"
    
    # Check for invalid characters in local part
    for char in local_part:
        if not (char.isalnum() or char in ['.', '_', '-', '+']):
            return False, "Email contains invalid characters"
    
    # Check for invalid characters in domain
    for char in domain:
        if not (char.isalnum() or char in ['.', '-']):
            return False, "Email domain contains invalid characters"
    
    return True, ""


def validate_phone(phone):
    """
    Validate phone number (10-digit Indian mobile number)
    Returns: (is_valid, error_message)
    """
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required"
    
    phone = phone.strip()
    
    # Remove common formatting characters
    cleaned_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    
    # Check if all remaining characters are digits
    if not cleaned_phone.isdigit():
        return False, "Phone number must contain only digits"
    
    # Check length (should be 10 digits for Indian numbers)
    if len(cleaned_phone) != 10:
        return False, "Phone number must be exactly 10 digits"
    
    # Check if starts with valid Indian mobile prefix (6, 7, 8, 9)
    first_digit = cleaned_phone[0]
    if first_digit not in ['6', '7', '8', '9']:
        return False, "Phone number must start with 6, 7, 8, or 9"
    
    return True, ""


def validate_name(name, field_name="Name"):
    """
    Validate name (first name, last name, etc.)
    Returns: (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, f"{field_name} is required"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, f"{field_name} must be at least 2 characters long"
    
    if len(name) > 50:
        return False, f"{field_name} must not exceed 50 characters"
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    for char in name:
        if not (char.isalpha() or char in [' ', '-', "'", '.']):
            return False, f"{field_name} contains invalid characters. Only letters, spaces, hyphens, apostrophes, and dots are allowed"
    
    # Check for consecutive spaces
    if '  ' in name:
        return False, f"{field_name} cannot contain consecutive spaces"
    
    # Check if name starts/ends with space or special character
    if name[0] in [' ', '-', "'", '.'] or name[-1] in [' ', '-', "'", '.']:
        return False, f"{field_name} cannot start or end with spaces or special characters"
    
    return True, ""


def validate_address(address, field_name="Address"):
    """
    Validate address
    Returns: (is_valid, error_message)
    """
    if not address or not isinstance(address, str):
        return False, f"{field_name} is required"
    
    address = address.strip()
    
    if len(address) < 10:
        return False, f"{field_name} must be at least 10 characters long"
    
    if len(address) > 200:
        return False, f"{field_name} must not exceed 200 characters"
    
    # Check for valid characters (alphanumeric, spaces, common address characters)
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-/#'()")
    for char in address:
        if char not in valid_chars:
            return False, f"{field_name} contains invalid characters"
    
    # Check for consecutive spaces
    if '  ' in address:
        return False, f"{field_name} cannot contain consecutive spaces"
    
    return True, ""


def validate_password(password):
    """
    Validate password
    Returns: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 50:
        return False, "Password must not exceed 50 characters"
    
    # Check for at least one letter
    has_letter = False
    for char in password:
        if char.isalpha():
            has_letter = True
            break
    
    if not has_letter:
        return False, "Password must contain at least one letter"
    
    return True, ""


def validate_aadhar(aadhar):
    """
    Validate Aadhar number (12 digits)
    Returns: (is_valid, error_message)
    """
    if not aadhar or not isinstance(aadhar, str):
        return False, "Aadhar number is required"
    
    aadhar = aadhar.strip().replace(' ', '').replace('-', '')
    
    if not aadhar.isdigit():
        return False, "Aadhar number must contain only digits"
    
    if len(aadhar) != 12:
        return False, "Aadhar number must be exactly 12 digits"
    
    # Aadhar should not be all same digits
    if len(set(aadhar)) == 1:
        return False, "Aadhar number cannot be all same digits"
    
    return True, ""


def validate_vehicle_number(vehicle_number):
    """
    Validate vehicle registration number (Indian format)
    Returns: (is_valid, error_message)
    """
    if not vehicle_number or not isinstance(vehicle_number, str):
        return False, "Vehicle number is required"
    
    vehicle_number = vehicle_number.strip().upper()
    
    if len(vehicle_number) < 8:
        return False, "Vehicle number is too short"
    
    if len(vehicle_number) > 15:
        return False, "Vehicle number is too long"
    
    # Basic check: should contain alphanumeric characters
    if not all(char.isalnum() or char in [' ', '-'] for char in vehicle_number):
        return False, "Vehicle number can only contain letters, numbers, spaces, and hyphens"
    
    return True, ""


def validate_vehicle_type(vehicle_type):
    """
    Validate vehicle type
    Returns: (is_valid, error_message)
    """
    if not vehicle_type or not isinstance(vehicle_type, str):
        return False, "Vehicle type is required"
    
    valid_types = ['bike', 'scooter', 'cycle', 'car']
    vehicle_type = vehicle_type.lower().strip()
    
    if vehicle_type not in valid_types:
        return False, f"Vehicle type must be one of: {', '.join(valid_types)}"
    
    return True, ""


def validate_parcel_weight(weight):
    """
    Validate parcel weight (must be positive number)
    Returns: (is_valid, error_message)
    """
    if weight is None:
        return False, "Parcel weight is required"
    
    try:
        weight_float = float(weight)
    except (ValueError, TypeError):
        return False, "Parcel weight must be a valid number"
    
    if weight_float <= 0:
        return False, "Parcel weight must be greater than 0"
    
    if weight_float > 1000:
        return False, "Parcel weight cannot exceed 1000 kg"
    
    return True, ""


def validate_parcel_type(parcel_type):
    """
    Validate parcel type
    Returns: (is_valid, error_message)
    """
    if not parcel_type or not isinstance(parcel_type, str):
        return False, "Parcel type is required"
    
    parcel_type = parcel_type.strip()
    
    if len(parcel_type) < 2:
        return False, "Parcel type must be at least 2 characters long"
    
    if len(parcel_type) > 50:
        return False, "Parcel type must not exceed 50 characters"
    
    # Check for valid characters
    if not all(char.isalnum() or char in [' ', '-', '/'] for char in parcel_type):
        return False, "Parcel type contains invalid characters"
    
    return True, ""


def validate_tracking_id(tracking_id):
    """
    Validate tracking ID format (should start with QP followed by digits)
    Returns: (is_valid, error_message)
    """
    if not tracking_id or not isinstance(tracking_id, str):
        return False, "Tracking ID is required"
    
    tracking_id = tracking_id.strip().upper()
    
    if len(tracking_id) < 3:
        return False, "Tracking ID is too short"
    
    if len(tracking_id) > 20:
        return False, "Tracking ID is too long"
    
    # Check if starts with QP
    if not tracking_id.startswith('QP'):
        return False, "Tracking ID must start with 'QP'"
    
    # Check if rest are digits
    if len(tracking_id) > 2:
        rest_part = tracking_id[2:]
        if not rest_part.isdigit():
            return False, "Tracking ID must have digits after 'QP'"
    
    return True, ""


def validate_status(status):
    """
    Validate delivery status
    Returns: (is_valid, error_message)
    """
    if not status or not isinstance(status, str):
        return False, "Status is required"
    
    valid_statuses = ['available', 'accepted', 'picked', 'on_the_way', 'delivered', 'completed']
    status = status.lower().strip()
    
    if status not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"
    
    return True, ""


def validate_amount(amount):
    """
    Validate payment amount
    Returns: (is_valid, error_message)
    """
    if amount is None:
        return False, "Amount is required"
    
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        return False, "Amount must be a valid number"
    
    if amount_float < 0:
        return False, "Amount cannot be negative"
    
    if amount_float > 1000000:
        return False, "Amount is too large"
    
    return True, ""


def validate_positive_integer(value, field_name="Value"):
    """
    Validate positive integer
    Returns: (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer"
    
    if int_value < 0:
        return False, f"{field_name} cannot be negative"
    
    return True, ""


def validate_password_confirmation(password, confirm_password):
    """
    Validate that password and confirm password match
    Returns: (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if not confirm_password or not isinstance(confirm_password, str):
        return False, "Password confirmation is required"
    
    if password != confirm_password:
        return False, "Passwords do not match"
    
    return True, ""


def validate_stops_list(stops):
    """
    Validate list of delivery stops
    Returns: (is_valid, error_message)
    """
    if not stops or not isinstance(stops, list):
        return False, "At least one delivery stop is required"
    
    if len(stops) == 0:
        return False, "At least one delivery stop is required"
    
    if len(stops) > 5:
        return False, "Maximum 5 stops are allowed"
    
    # Validate each stop
    for i, stop in enumerate(stops, 1):
        if not isinstance(stop, dict):
            return False, f"Stop {i} is invalid"
        
        # Validate drop address
        drop_address = stop.get('drop_address') or stop.get('dropAddress')
        is_valid, error = validate_address(drop_address, f"Stop {i} drop address")
        if not is_valid:
            return False, error
        
        # Validate receiver name
        receiver_name = stop.get('receiver_name') or stop.get('receiverName')
        is_valid, error = validate_name(receiver_name, f"Stop {i} receiver name")
        if not is_valid:
            return False, error
        
        # Validate receiver phone
        receiver_phone = stop.get('receiver_phone') or stop.get('receiverPhone')
        is_valid, error = validate_phone(receiver_phone)
        if not is_valid:
            return False, f"Stop {i} receiver phone: {error}"
    
    return True, ""


def validate_stop_number(stop_number, total_stops):
    """
    Validate stop number for multi-stop delivery
    Returns: (is_valid, error_message)
    """
    is_valid, error = validate_positive_integer(stop_number, "Stop number")
    if not is_valid:
        return False, error
    
    stop_num = int(stop_number)
    
    if stop_num < 1:
        return False, "Stop number must be at least 1"
    
    if total_stops and stop_num > total_stops:
        return False, f"Stop number cannot exceed total stops ({total_stops})"
    
    return True, ""


def validate_total_stops(total_stops):
    """
    Validate total number of stops
    Returns: (is_valid, error_message)
    """
    is_valid, error = validate_positive_integer(total_stops, "Total stops")
    if not is_valid:
        return False, error
    
    stops = int(total_stops)
    
    if stops < 1:
        return False, "At least one stop is required"
    
    if stops > 5:
        return False, "Maximum 5 stops are allowed"
    
    return True, ""


def validate_partner_id(partner_id):
    """
    Validate partner ID format (PARTNER####)
    Returns: (is_valid, error_message)
    """
    if not partner_id or not isinstance(partner_id, str):
        return False, "Partner ID is required"
    
    partner_id = partner_id.strip().upper()
    
    if len(partner_id) < 8:
        return False, "Partner ID is too short"
    
    if len(partner_id) > 15:
        return False, "Partner ID is too long"
    
    # Check if starts with PARTNER
    if not partner_id.startswith('PARTNER'):
        return False, "Partner ID must start with 'PARTNER'"
    
    # Check if rest are digits
    if len(partner_id) > 7:
        rest_part = partner_id[7:]
        if not rest_part.isdigit():
            return False, "Partner ID must have digits after 'PARTNER'"
    
    return True, ""


def validate_payment_method(payment_method):
    """
    Validate payment method
    Returns: (is_valid, error_message)
    """
    if not payment_method or not isinstance(payment_method, str):
        return False, "Payment method is required"
    
    valid_methods = ['online', 'cash']
    payment_method = payment_method.lower().strip()
    
    if payment_method not in valid_methods:
        return False, f"Payment method must be one of: {', '.join(valid_methods)}"
    
    return True, ""


def validate_payment_status(payment_status):
    """
    Validate payment status
    Returns: (is_valid, error_message)
    """
    if not payment_status or not isinstance(payment_status, str):
        return False, "Payment status is required"
    
    valid_statuses = ['pending', 'paid', 'pending_cash']
    payment_status = payment_status.lower().strip()
    
    if payment_status not in valid_statuses:
        return False, f"Payment status must be one of: {', '.join(valid_statuses)}"
    
    return True, ""


def validate_partner_status(status):
    """
    Validate partner status (online/offline)
    Returns: (is_valid, error_message)
    """
    if not status or not isinstance(status, str):
        return False, "Status is required"
    
    valid_statuses = ['online', 'offline']
    status = status.lower().strip()
    
    if status not in valid_statuses:
        return False, f"Partner status must be one of: {', '.join(valid_statuses)}"
    
    return True, ""


def validate_delivery_id(delivery_id):
    """
    Validate delivery ID format
    Returns: (is_valid, error_message)
    """
    return validate_tracking_id(delivery_id)


def validate_non_empty_string(value, field_name="Field"):
    """
    Validate that a string is not empty
    Returns: (is_valid, error_message)
    """
    if not value or not isinstance(value, str):
        return False, f"{field_name} is required"
    
    if not value.strip():
        return False, f"{field_name} cannot be empty"
    
    return True, ""


def validate_list_not_empty(value_list, field_name="List"):
    """
    Validate that a list is not empty
    Returns: (is_valid, error_message)
    """
    if not value_list or not isinstance(value_list, list):
        return False, f"{field_name} is required and must be a list"
    
    if len(value_list) == 0:
        return False, f"{field_name} cannot be empty"
    
    return True, ""


def validate_file_extension(filename, allowed_extensions=None):
    """
    Validate file extension (for optional file uploads)
    Returns: (is_valid, error_message)
    """
    if not filename:
        return True, ""  # Empty filename is allowed for optional uploads
    
    if not isinstance(filename, str):
        return False, "Invalid filename"
    
    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf']
    
    # Extract extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension not in allowed_extensions:
        return False, f"File extension must be one of: {', '.join(allowed_extensions)}"
    
    return True, ""


def validate_distance(distance):
    """
    Validate distance value (in kilometers)
    Returns: (is_valid, error_message)
    """
    if distance is None:
        return False, "Distance is required"
    
    try:
        distance_float = float(distance)
    except (ValueError, TypeError):
        return False, "Distance must be a valid number"
    
    if distance_float < 0:
        return False, "Distance cannot be negative"
    
    if distance_float > 100:
        return False, "Distance cannot exceed 100 km"
    
    return True, ""


def validate_string_length(value, min_length, max_length, field_name="Field"):
    """
    Generic string length validator
    Returns: (is_valid, error_message)
    """
    if not value or not isinstance(value, str):
        return False, f"{field_name} is required"
    
    value = value.strip()
    length = len(value)
    
    if length < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"
    
    if length > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"
    
    return True, ""


def validate_numeric_range(value, min_value, max_value, field_name="Value"):
    """
    Validate numeric value is within range
    Returns: (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"
    
    if num_value < min_value:
        return False, f"{field_name} must be at least {min_value}"
    
    if num_value > max_value:
        return False, f"{field_name} must not exceed {max_value}"
    
    return True, ""


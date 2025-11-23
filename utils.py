import re
from datetime import datetime, date

class ValidationError(Exception):
    pass

def validate_email(email):
    if not email:
        raise ValidationError("Email is required")
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    
    return True

def validate_phone(phone):
    if not phone:
        return True
    
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    if not cleaned.isdigit() or len(cleaned) < 10 or len(cleaned) > 15:
        raise ValidationError("Invalid phone number format (should be 10-15 digits)")
    
    return True

def validate_password(password):
    if not password:
        raise ValidationError("Password is required")
    
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long")
    
    return True

def validate_date(date_str, format='%Y-%m-%d', allow_future=False, allow_past=True):
    if not date_str:
        raise ValidationError("Date is required")
    
    try:
        parsed_date = datetime.strptime(date_str, format).date()
    except ValueError:
        raise ValidationError(f"Invalid date format (expected {format})")
    
    today = date.today()
    
    if not allow_future and parsed_date > today:
        raise ValidationError("Date cannot be in the future")
    
    if not allow_past and parsed_date < today:
        raise ValidationError("Date cannot be in the past")
    
    return parsed_date

def validate_required_fields(data, required_fields):
    missing = []
    for field in required_fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    
    return True

def validate_time_range(start_time, end_time):
    if not start_time or not end_time:
        raise ValidationError("Start time and end time are required")
    
    if end_time <= start_time:
        raise ValidationError("End time must be after start time")
    
    return True

def validate_gender(gender):
    if not gender:
        return True
    
    allowed = ['Male', 'Female', 'Other']
    if gender not in allowed:
        raise ValidationError(f"Gender must be one of: {', '.join(allowed)}")
    
    return True

def validate_length(value, field_name, min_length=None, max_length=None):
    if not value:
        return True
    
    length = len(value)
    
    if min_length and length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if max_length and length > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    
    return True

def sanitize_input(value):
    if isinstance(value, str):
        return value.strip()
    return value

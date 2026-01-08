import re
from typing import Dict, List


class ValidationError(Exception):
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        super().__init__("Validation failed")


def validate_email_format(email: str) -> bool:
    """Simple but effective email validation"""
    if not email or not isinstance(email, str):
        return False

    email = email.strip()

    if '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False

    local_part, domain = parts
    if not local_part or not domain:
        return False
    if '.' not in domain:
        return False
    domain_parts = domain.split('.')
    if len(domain_parts[-1]) < 2:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_required_fields(data: Dict, required_fields: List[str]) -> Dict[str, List[str]]:
    """Validate that all required fields are present"""
    errors = {}

    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            if "required" not in errors:
                errors["required"] = []
            errors["required"].append(f"Field '{field}' is required")

    return errors


def validate_user_registration(data: Dict) -> Dict[str, List[str]]:
    """Validate user registration data"""
    errors = {}
    required_errors = validate_required_fields(data, ['email', 'password', 'username'])
    if required_errors:
        errors.update(required_errors)
    if 'email' in data and data['email']:
        email = str(data['email']).strip()
        if not validate_email_format(email):
            if "email" not in errors:
                errors["email"] = []
            errors["email"].append(f"Invalid email format: '{email}'")
    if 'password' in data and data['password']:
        password = str(data['password'])
        if len(password) < 8:
            if "password" not in errors:
                errors["password"] = []
            errors["password"].append("Password must be at least 8 characters long")
    if 'username' in data and data['username']:
        username = str(data['username']).strip()
        if len(username) < 3:
            if "username" not in errors:
                errors["username"] = []
            errors["username"].append("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            if "username" not in errors:
                errors["username"] = []
            errors["username"].append("Username can only contain letters, numbers and underscores")

    return errors


def validate_ad_creation(data: Dict) -> Dict[str, List[str]]:
    """Validate ad creation data"""
    errors = {}
    required_errors = validate_required_fields(data, ['title'])
    if required_errors:
        errors.update(required_errors)
    if 'title' in data and data['title']:
        title = str(data['title']).strip()
        if len(title) < 3:
            if "title" not in errors:
                errors["title"] = []
            errors["title"].append("Title must be at least 3 characters long")
        if len(title) > 200:
            if "title" not in errors:
                errors["title"] = []
            errors["title"].append("Title must not exceed 200 characters")
    if 'description' in data and data['description']:
        description = str(data['description']).strip()
        if len(description) > 2000:
            if "description" not in errors:
                errors["description"] = []
            errors["description"].append("Description must not exceed 2000 characters")

    return errors


def validate_login(data: Dict) -> Dict[str, List[str]]:
    """Validate login data"""
    errors = {}
    required_errors = validate_required_fields(data, ['email', 'password'])
    if required_errors:
        errors.update(required_errors)

    return errors


def validate_ad_update(data: Dict) -> Dict[str, List[str]]:
    """Validate ad update data"""
    errors = {}
    if not any(key in data for key in ['title', 'description']):
        errors["general"] = ["At least one field (title or description) must be provided for update"]
    if 'title' in data and data['title']:
        title = str(data['title']).strip()
        if len(title) < 3:
            if "title" not in errors:
                errors["title"] = []
            errors["title"].append("Title must be at least 3 characters long")
        if len(title) > 200:
            if "title" not in errors:
                errors["title"] = []
            errors["title"].append("Title must not exceed 200 characters")
    if 'description' in data and data['description']:
        description = str(data['description']).strip()
        if len(description) > 2000:
            if "description" not in errors:
                errors["description"] = []
            errors["description"].append("Description must not exceed 2000 characters")

    return errors
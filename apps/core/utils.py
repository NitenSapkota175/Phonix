"""
Shared utility functions for the Phonix platform.
"""
import string
import random
from decimal import Decimal, ROUND_HALF_UP


def generate_random_code(length=8, chars=string.ascii_uppercase + string.digits):
    """Generate a random alphanumeric code of given length."""
    return ''.join(random.choices(chars, k=length))


def generate_unique_code(model_class, field_name, length=8):
    """
    Generate a unique code that doesn't already exist in the database.

    Example:
        code = generate_unique_code(User, 'referral_code', 8)
    """
    while True:
        code = generate_random_code(length)
        if not model_class.objects.filter(**{field_name: code}).exists():
            return code


def round_decimal(value, places=2):
    """Round a Decimal to given decimal places using ROUND_HALF_UP."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    quantize_str = Decimal('0.' + '0' * places)
    return value.quantize(quantize_str, rounding=ROUND_HALF_UP)


def calculate_percentage(amount, rate_percent):
    """
    Calculate percentage of amount.

    Args:
        amount: Decimal or float
        rate_percent: Percentage as decimal (e.g. 5 for 5%)

    Returns:
        Decimal result
    """
    amount = Decimal(str(amount))
    rate = Decimal(str(rate_percent)) / Decimal('100')
    return round_decimal(amount * rate)


def get_weekday_name(weekday_int):
    """Convert Python weekday int (0=Mon, 6=Sun) to name."""
    names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return names[weekday_int]


def is_business_day(dt=None):
    """Return True if the given datetime (or now) is Mon–Fri."""
    from django.utils import timezone
    dt = dt or timezone.now()
    return dt.weekday() < 5  # 0=Mon, 4=Fri, 5=Sat, 6=Sun


def mask_email(email):
    """Mask email for display: user@example.com → u***@example.com"""
    try:
        local, domain = email.split('@')
        masked = local[0] + '***'
        return f'{masked}@{domain}'
    except Exception:
        return email


def build_referral_link(request, referral_code):
    """Build a full absolute referral registration URL."""
    from django.urls import reverse
    base = request.build_absolute_uri(reverse('accounts:register'))
    return f'{base}?ref={referral_code}'

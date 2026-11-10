import re
from math import isqrt
from django.core.exceptions import ValidationError


def validate_pages_to_print(value):
    if value == "" or value is None:
        return
    code = 'invalid'
    if not re.search(r'^\d+(?:-\d+)?(,\d+(?:-\d+)?)*$', str(value)):
        raise ValidationError(f'Invalid page selection string: {value}', code=code)
    parts = [part.split('-') for part in value.split(',')]
    for part in parts:
        if int(part[0]) > int(part[-1]) or int(part[0]) < 1:
            raise ValidationError(f'Invalid page range: {part[0]}-{part[-1]}', code=code)


def validate_n_up(value: int):
    if isqrt(value) ** 2 == value:
        return
    if value % 2 == 0 and 2 * (isqrt(value // 2) ** 2) == value:
        return
    raise ValidationError("n must be a perfect square or a perfect square times 2")


def validate_margins(value: float):
    if value < 0.0 or value > 100.0:
        raise ValidationError(f"Margin must be between 0.0 and 100.0 (got {value})")

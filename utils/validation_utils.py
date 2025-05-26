import re

def is_number_like(value):
    if not isinstance(value, str):
        return False
    cleaned = value.replace(" ", "").replace(",", ".")
    return bool(re.match(r'^\d+(\.\d+)?$', cleaned.strip()))

def is_unit_like(value):
    if not isinstance(value, str):
        return False
    units = ['g/dL', 'mg/L', 'µm³', 'mm³', '%', 'x10⁶', 'x10³', 'g/L', 'pg', 'fL', 'µL', 'g/L', '/mm³']
    return any(unit in value for unit in units) or bool(re.match(r'^[a-zA-Zµ/°³²%]+$', value.strip()))

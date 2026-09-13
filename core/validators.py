import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    """Valida que la extensión del archivo sea permitida."""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError(
            f'Formato no permitido. Solo se permiten: {", ".join(valid_extensions)}.'
        )
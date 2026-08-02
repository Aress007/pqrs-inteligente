# ============================================================
# CLASIFICADOR DE PQRS - VERSIÓN LIGERA (solo palabras clave)
# ============================================================
# Esta versión no usa transformers para ahorrar memoria en producción.
# Clasifica por palabras clave de forma rápida y eficiente.
# ============================================================

def classify_text_zero_shot(texto):
    """
    Clasifica el texto en una de las cuatro categorías usando palabras clave.
    Retorna: 'peticion', 'queja', 'reclamo' o 'sugerencia'
    """
    t = texto.lower()
    
    # Palabras clave para queja
    if any(p in t for p in [
        'groser', 'mala atención', 'lento', 'queja', 'demora', 
        'insatisfecho', 'mal servicio', 'descortés', 'ignoraron', 'tardaron'
    ]):
        return 'queja'
    
    # Palabras clave para reclamo
    if any(p in t for p in [
        'reclamo', 'dañado', 'roto', 'devolución', 'dinero', 
        'defectuoso', 'equivocación', 'error', 'cobro indebido', 'mal estado'
    ]):
        return 'reclamo'
    
    # Palabras clave para sugerencia
    if any(p in t for p in [
        'sugerencia', 'mejorar', 'propongo', 'sería bueno', 
        'recomiendo', 'podrían', 'implementar', 'agregar'
    ]):
        return 'sugerencia'
    
    # Por defecto, petición
    return 'peticion'
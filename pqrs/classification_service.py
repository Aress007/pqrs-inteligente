# =====CLASIFICADOR DE PQRS CON TRANSFORMERS (mDeBERTa)=====
# 
# =====Modelo multilingüe Soporta español, inglés, etc.=====

from transformers import pipeline

# Variables globales: el modelo se carga UNA SOLA VEZ
_classifier = None
_LABELS = None
_MAPEO = None

def _cargar_modelo():
    global _classifier, _LABELS, _MAPEO
    
    if _classifier is not None:
        return
    
    try:
        print("[INFO] Cargando modelo de Hugging Face (puede tomar unos segundos la primera vez)...")
        _classifier = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
            device=-1  
        )
        
        _LABELS = [
            "petición de información o solicitud de servicio",
            "queja por mala atención o inconformidad",
            "reclamo por incumplimiento, cobro o producto defectuoso",
            "sugerencia para mejorar el servicio"
        ]
        
        _MAPEO = {
            "petición de información o solicitud de servicio": "peticion",
            "queja por mala atención o inconformidad": "queja",
            "reclamo por incumplimiento, cobro o producto defectuoso": "reclamo",
            "sugerencia para mejorar el servicio": "sugerencia"
        }
        print("[INFO] Modelo cargado exitosamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el modelo: {e}")
        print("[INFO] Usando clasificador por palabras clave como fallback.")
        _classifier = None

def classify_text_zero_shot(texto):
    """
    Clasifica el texto usando zero-shot classification con mDeBERTa.
    Retorna la categoría ('peticion', 'queja', 'reclamo', 'sugerencia').
    Si el modelo falla o no hay confianza suficiente, usa palabras clave.
    """
    _cargar_modelo()
    
    if _classifier is None or _LABELS is None:
        return _clasificacion_palabras_clave(texto)
    
    try:
        resultado = _classifier(texto, _LABELS, multi_label=False)
        mejor_label = resultado["labels"][0]
        score = resultado["scores"][0]
        
        print(f"[DEBUG] IA -> {mejor_label} | confianza: {score:.2f}")
        
        if score < 0.60:
            print("[INFO] Confianza baja, usando clasificador por palabras clave.")
            return _clasificacion_palabras_clave(texto)
        
        return _MAPEO.get(mejor_label, "peticion")
        
    except Exception as e:
        print(f"[ERROR] Excepción en clasificación IA: {e}")
        return _clasificacion_palabras_clave(texto)

# ======CLASIFICADOR POR PALABRAS CLAVE======

def _clasificacion_palabras_clave(texto):
    """Versión de respaldo: clasifica por palabras clave"""
    t = texto.lower()
    if any(p in t for p in ['groser', 'mala atención', 'lento', 'queja', 'demora', 'insatisfecho', 'mal servicio', 'descortés', 'ignoraron', 'tardaron']):
        return 'queja'
    if any(p in t for p in ['reclamo', 'dañado', 'roto', 'devolución', 'dinero', 'defectuoso', 'equivocación', 'error', 'cobro indebido', 'mal estado']):
        return 'reclamo'
    if any(p in t for p in ['sugerencia', 'mejorar', 'propongo', 'sería bueno', 'recomiendo', 'podrían', 'implementar', 'agregar']):
        return 'sugerencia'
    return 'peticion'
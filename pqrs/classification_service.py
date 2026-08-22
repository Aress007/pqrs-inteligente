# ============================================================
# CLASIFICADOR DE PQRS CON API DE HUGGING FACE (LIVIANO)
# ============================================================
# No usa transformers localmente. Solo hace peticiones HTTP.
# Consume 0 MB de RAM en el servidor de RENDER.
# ============================================================

import os
import requests

# ============================================================
# CONFIGURACIÓN DE LA API
# ============================================================
# Obtener el token en: https://huggingface.co/settings/tokens
HF_TOKEN = os.getenv("HF_TOKEN", "")  # variable definida en Render
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"  # Modelo zero-shot
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# Etiquetas para clasificación
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

# ============================================================
# FUNCIÓN PRINCIPAL DE CLASIFICACIÓN
# ============================================================
def classify_text_zero_shot(texto):
    """
    Clasifica el texto usando la API de Hugging Face.
    Si la API falla, excede el límite o da baja confianza, usa palabras clave.
    """
    if not HF_TOKEN:
        print("[WARNING] HF_TOKEN no configurado. Usando clasificador por palabras clave.")
        return _clasificacion_palabras_clave(texto)
    
    payload = {
        "inputs": texto,
        "parameters": {"candidate_labels": _LABELS, "multi_label": False}
    }
    
    try:
        print("[INFO] Enviando petición a Hugging Face API...")
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
        
        # Si el modelo está cargándose (503), Hugging Face devuelve este código
        if response.status_code == 503:
            print("[INFO] El modelo se está cargando en Hugging Face. Usando fallback por ahora.")
            return _clasificacion_palabras_clave(texto)
        
        response.raise_for_status()
        resultado = response.json()

        # La API actual devuelve una lista de resultados
        if not isinstance(resultado, list) or not resultado:
            print(f"[ERROR] Respuesta inesperada de Hugging Face: {resultado}")
            return _clasificacion_palabras_clave(texto)

        # Obtener el resultado con mayor puntuación
        mejor_resultado = resultado[0]

        if not isinstance(mejor_resultado, dict):
            print(f"[ERROR] Formato inesperado: {mejor_resultado}")
            return _clasificacion_palabras_clave(texto)

        mejor_label = mejor_resultado.get("label")
        score = mejor_resultado.get("score", 0)

        if not mejor_label:
            print(f"[ERROR] No se encontró la etiqueta en la respuesta: {resultado}")
            return _clasificacion_palabras_clave(texto)

        print(f"[DEBUG] IA API -> {mejor_label} | confianza: {score:.2f}")

        # Si la confianza es baja, usa el clasificador de respaldo
        if score < 0.60:
            print("[INFO] Confianza baja. Usando clasificador por palabras clave.")
            return _clasificacion_palabras_clave(texto)

        return _MAPEO.get(mejor_label, "peticion")
        
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout en Hugging Face API. Usando fallback.")
        return _clasificacion_palabras_clave(texto)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error en Hugging Face API: {e}")
        return _clasificacion_palabras_clave(texto)
    except Exception as e:
        print(f"[ERROR] Excepción inesperada: {e}")
        return _clasificacion_palabras_clave(texto)


# ============================================================
# CLASIFICADOR POR PALABRAS CLAVE (FALLBACK)
# ============================================================
def _clasificacion_palabras_clave(texto):
    """Versión de respaldo: clasifica por palabras clave"""
    t = texto.lower()
    
    # Palabras clave para queja
    if any(p in t for p in ['groser', 'mala atención', 'lento', 'queja', 'demora', 'insatisfecho', 'mal servicio', 'descortés', 'ignoraron', 'tardaron']):
        return 'queja'
    
    # Palabras clave para reclamo
    if any(p in t for p in ['reclamo', 'dañado', 'roto', 'devolución', 'dinero', 'defectuoso', 'equivocación', 'error', 'cobro indebido', 'mal estado']):
        return 'reclamo'
    
    # Palabras clave para sugerencia (incluye elogios)
    if any(p in t for p in ['sugerencia', 'mejorar', 'propongo', 'sería bueno', 'recomiendo', 'podrían', 'implementar', 'agregar', 'excelente', 'felicitaciones', 'buen servicio', 'perfecto', 'genial']):
        return 'sugerencia'
    
    # Por defecto: petición
    return 'peticion'
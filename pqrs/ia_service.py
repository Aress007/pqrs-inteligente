import os
import requests
import random

# ============================================================
# CONFIGURACIÓN DE LA API DE HUGGING FACE (para el chatbot)
# ============================================================
HF_TOKEN = os.getenv("HF_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# ============================================================
# CHATBOT CON HUGGING FACE API (FLAN-T5 = T5. Text-To-Text Transfer Transformer. / FLAN. Fine-tuned Language Net, entrenamiento adicional)
# ============================================================
CHATBOT_URL = "https://router.huggingface.co/v1/chat/completions"

def chat_bot(mensaje_usuario, historial=None, contexto=""):
    """
    Chatbot que usa la API de Hugging Face con FLAN-T5.
    Si la API falla, usa el fallback local por palabras clave.
    """
    if not HF_TOKEN:
        print("[CHATBOT] Token no configurado, usando fallback local.")
        return _chatbot_fallback_local(mensaje_usuario)
    
    # Construir el prompt para FLAN-T5
    # FLAN-T5:
    # T5 → Text-To-Text Transfer Transformer.
    # FLAN → Fine-tuned Language Net, entrenamiento adicional
    # para mejorar el seguimiento de instrucciones.
    #
    # En este proyecto se utiliza para procesar y clasificar
    # el texto de las solicitudes PQRS mediante instrucciones.
    prompt = f"Responde de manera amable y útil a la siguiente pregunta o mensaje de un usuario sobre PQRS (Peticiones, Quejas, Reclamos, Sugerencias). Si no sabes la respuesta, sugiere contactar con soporte. Mensaje del usuario: {mensaje_usuario}"
    
    payload = {
        "model": "openai/gpt-oss-120b:fastest",
        "messages": [
            {
                "role": "system",
                "content": f"""
        Eres el asistente virtual de un sistema de PQRS.

        Debes responder en español de manera amable, clara y breve.

        Puedes ayudar al usuario con:
        - Estado de sus PQRS.
        - Información de sus radicados.
        - Respuestas recibidas en sus PQRS.
        - Cómo crear una PQRS.
        - Preguntas generales sobre el sistema.

        REGLAS IMPORTANTES:

        1. Solo puedes proporcionar información de las PQRS
        que aparecen en el contexto proporcionado por el sistema.

        2. Nunca inventes estados, radicados, respuestas,
        fechas o información que no esté en el contexto.

        3. Si no se encuentra un radicado, indícale al usuario
        que no fue encontrado.

        4. No reveles información de PQRS pertenecientes
        a otros usuarios.

        5. Si el usuario pregunta quién creó una PQRS,
        no reveles datos personales innecesarios.
        Puedes indicar que el radicado pertenece al usuario
        autenticado cuando corresponda.

        6. Si no sabes la respuesta, indícale al usuario
        que debe contactar con soporte.

        CONTEXTO DE LA BASE DE DATOS:

        {contexto}
        """
            },
            {
                "role": "user",
                "content": mensaje_usuario
            }
        ],
        "max_tokens": 300,
        "temperature": 0.7,
        "stream": False
    }
        
    try:
        print("[CHATBOT] Enviando petición a Hugging Face API...")
        response = requests.post(CHATBOT_URL, headers=HEADERS, json=payload, timeout=15)
        
        if response.status_code == 503:
            print("[CHATBOT] El modelo se está cargando en Hugging Face. Usando fallback local.")
            return _chatbot_fallback_local(mensaje_usuario)
        
        response.raise_for_status()
        resultado = response.json()

        # La API de chat devuelve la respuesta dentro de choices
        if isinstance(resultado, dict):
            choices = resultado.get("choices", [])

            if choices and isinstance(choices[0], dict):
                message = choices[0].get("message", {})

                if isinstance(message, dict):
                    respuesta = message.get("content", "").strip()

                    if respuesta:
                        print(f"[CHATBOT] Respuesta IA: {respuesta[:80]}...")
                        return respuesta

                    # Si el modelo terminó por límite de tokens,
                    # no mostrar el razonamiento interno.
                    if choices[0].get("finish_reason") == "length":
                        print(
                            "[CHATBOT] La respuesta alcanzó el límite de tokens. "
                            "Usando fallback local."
                        )
                        return _chatbot_fallback_local(mensaje_usuario)

        print(f"[CHATBOT] Respuesta inesperada de la API: {resultado}")
        print("[CHATBOT] Usando fallback local.")

        return _chatbot_fallback_local(mensaje_usuario)
        
        # Si no hay respuesta válida, usar fallback
        print("[CHATBOT] Respuesta vacía de la API. Usando fallback local.")
        return _chatbot_fallback_local(mensaje_usuario)
        
    except requests.exceptions.Timeout:
        print("[CHATBOT] Timeout en Hugging Face API. Usando fallback local.")
        return _chatbot_fallback_local(mensaje_usuario)
    except requests.exceptions.RequestException as e:
        print(f"[CHATBOT] Error en Hugging Face API: {e}")
        return _chatbot_fallback_local(mensaje_usuario)
    except Exception as e:
        print(f"[CHATBOT] Excepción inesperada: {e}")
        return _chatbot_fallback_local(mensaje_usuario)


# ============================================================
# CHATBOT FALLBACK LOCAL (palabras clave)
# ============================================================
def _chatbot_fallback_local(mensaje_usuario):
    """Versión de respaldo: responde por palabras clave"""
    mensaje = mensaje_usuario.lower().strip()
    
    respuestas = {
        'hola': ['¡Hola! ¿Cómo puedo ayudarte?', '¡Buen día! ¿En qué te puedo asistir?', 'Hola, soy el asistente virtual.'],
        'gracias': ['¡De nada! Estoy para servirte.', 'Fue un placer ayudarte.', '¡A tus órdenes!'],
        'queja': ['Lamento que hayas tenido una mala experiencia. ¿Puedes darme más detalles?', 
                 'Entiendo tu incomodidad. Vamos a resolverlo juntos.'],
        'reclamo': ['Recibimos tu reclamo. ¿Puedes proporcionar el número de radicado?',
                   'Un asesor se pondrá en contacto contigo pronto.'],
        'sugerencia': ['¡Gracias por tu sugerencia! La tendremos en cuenta.',
                       'Tu opinión es muy valiosa. La enviaremos al área correspondiente.'],
        'estado': ['Para consultar el estado de tu PQRS, necesito el número de radicado.',
                   'Puedes ver el estado en "Mis Solicitudes" dentro de tu cuenta.'],
        'adios': ['¡Hasta luego! Que tengas un excelente día.', '¡Chao! No dudes en volver.'],
        'ayuda': ['Puedo ayudarte con: estado de PQRS, cómo crear una PQRS, o responder preguntas generales.',
                 'Estoy aquí para orientarte. ¿Sobre qué tema necesitas ayuda?'],
        'crear': ['Para crear una PQRS, inicia sesión y haz clic en "Nueva PQRS". Completa el formulario y el sistema la clasificará automáticamente.',
                 'Puedes crear una PQRS desde el menú principal. El sistema te guiará paso a paso.']
    }
    
    if any(p in mensaje for p in ['hola', 'buen día', 'buenas']):
        return random.choice(respuestas['hola'])
    elif any(p in mensaje for p in ['gracias', 'agradezco']):
        return random.choice(respuestas['gracias'])
    elif any(p in mensaje for p in ['queja', 'mal servicio', 'inconformidad']):
        return random.choice(respuestas['queja'])
    elif any(p in mensaje for p in ['reclamo', 'problema', 'dañado', 'error', 'cobro']):
        return random.choice(respuestas['reclamo'])
    elif any(p in mensaje for p in ['sugerencia', 'mejorar', 'propongo', 'idea']):
        return random.choice(respuestas['sugerencia'])
    elif any(p in mensaje for p in ['estado', 'radicado', 'seguimiento']):
        return random.choice(respuestas['estado'])
    elif any(p in mensaje for p in ['adios', 'chao', 'hasta luego']):
        return random.choice(respuestas['adios'])
    elif any(p in mensaje for p in ['ayuda', 'funciones', 'qué haces']):
        return random.choice(respuestas['ayuda'])
    elif any(p in mensaje for p in ['crear', 'radicar', 'nueva pqrs']):
        return random.choice(respuestas['crear'])
    else:
        return "No entendí tu mensaje. Puedes preguntarme sobre: estado de PQRS, cómo crear una PQRS, o simplemente saludarme."


# ============================================================
# ANÁLISIS DE SENTIMIENTOS LOCAL (por palabras clave) ( El place holder puede adaptarse a cualquier función a futuro de la empresa)
# ============================================================
def analizar_sentimiento(texto):
    """
    Analiza el sentimiento de un texto usando palabras clave.
    Retorna: 'positivo', 'negativo', 'neutral'.
    """
    t = texto.lower()
    positivas = ['excelente', 'buen', 'buena', 'bien', 'perfecto', 'genial', 'maravilloso', 'fantástico', 'satisfecho', 'agradecido', 'recomiendo']
    negativas = ['malo', 'mala', 'pésimo', 'terrible', 'horrible', 'decepcionado', 'insatisfecho', 'problema', 'error', 'falla', 'dañado', 'roto', 'demora', 'grosero']
    
    pos_count = sum(1 for p in positivas if p in t)
    neg_count = sum(1 for p in negativas if p in t)
    
    if pos_count > neg_count:
        return 'positivo'
    elif neg_count > pos_count:
        return 'negativo'
    else:
        return 'neutral'
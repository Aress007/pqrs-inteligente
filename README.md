# PQRS Inteligente

Sistema web para la gestión de **Peticiones, Quejas, Reclamos y Sugerencias (PQRS)**, desarrollado con Django e integrado con servicios de Inteligencia Artificial para la clasificación automática de solicitudes y un chatbot con contexto relacionado con PQRS.

El sistema permite centralizar la recepción, seguimiento y gestión de solicitudes realizadas por los clientes hacia las empresas, incorporando herramientas de trazabilidad, control de tiempos de respuesta, notificaciones, almacenamiento de archivos y gestión de suscripciones.

## Características principales

* Registro unificado de usuarios como **cliente** o **empresa**.
* Inicio de sesión y autenticación mediante Django.
* Recuperación y cambio de contraseña mediante correo electrónico.
* Envío de notificaciones mediante SendGrid.
* Creación y gestión de PQRS.
* Clasificación automática de PQRS mediante Inteligencia Artificial.
* Clasificación **Zero-Shot** utilizando el modelo `facebook/bart-large-mnli`.
* Análisis básico de sentimiento mediante palabras clave.
* Dashboard empresarial con indicadores y gráficos.
* Filtros y búsqueda de PQRS.
* Exportación de información a formato CSV.
* Chatbot con contexto relacionado con las PQRS del usuario.
* Control de tiempos de atención mediante un **SLA de 72 horas**.
* Historial de trazabilidad de las PQRS.
* Archivos adjuntos en PQRS y respuestas.
* Almacenamiento de archivos e imágenes mediante Cloudinary.
* Integración con ePayco en ambiente **sandbox** para pruebas de suscripción.
* Copias de seguridad y restauración de información en formato JSON.
* Interfaz adaptable para computadores, tabletas y dispositivos móviles.
* Despliegue de la aplicación en Render.

## Tecnologías utilizadas

| Categoría                | Tecnología                    |
| ------------------------ | ----------------------------- |
| Lenguaje                 | Python 3.13                   |
| Framework Backend        | Django 6.0.7                  |
| Servidor de aplicaciones | Gunicorn 23.0.0               |
| Frontend                 | HTML5, CSS3, Bootstrap 5.3    |
| Iconos                   | Bootstrap Icons               |
| Gráficos                 | Chart.js 4.5.1                |
| Base de datos            | SQLite 3.45.3                 |
| Inteligencia Artificial  | Hugging Face Inference API    |
| Clasificación IA         | `facebook/bart-large-mnli`    |
| Chatbot                  | `openai/gpt-oss-120b:fastest` |
| Almacenamiento           | Cloudinary                    |
| Correo electrónico       | SendGrid                      |
| Pagos                    | ePayco Sandbox                |
| Despliegue               | Render                        |
| Control de versiones     | Git / GitHub                  |

## Arquitectura

El sistema utiliza la arquitectura **MVT (Model-View-Template)** proporcionada por Django.

Las principales aplicaciones del proyecto son:

* `core`: funcionalidades generales del sistema.
* `empresas`: gestión de empresas y planes.
* `pqrs`: gestión de PQRS, clasificación mediante IA, chatbot y trazabilidad.
* `usuarios`: autenticación, perfiles, recuperación de contraseña y pagos.

### Servicios externos

* **Cloudinary:** almacenamiento de imágenes, archivos adjuntos, fotos de perfil y logos.
* **SendGrid:** envío de correos electrónicos.
* **Hugging Face:** clasificación Zero-Shot y funcionamiento del chatbot.
* **ePayco:** procesamiento de pagos en ambiente sandbox.

# Inteligencia Artificial

## Clasificación de PQRS

El sistema utiliza clasificación **Zero-Shot** mediante el modelo:

facebook/bart-large-mnli

Las solicitudes son clasificadas en cuatro categorías:

* Petición
* Queja
* Reclamo
* Sugerencia

El texto de la solicitud se envía al servicio de Inteligencia Artificial junto con las categorías disponibles. El sistema selecciona la categoría con mayor puntuación de confianza.

Cuando la confianza obtenida es inferior al umbral establecido o el servicio externo no está disponible, se utiliza un mecanismo de respaldo basado en palabras clave.

## Análisis de sentimiento

El sistema realiza una clasificación básica del sentimiento de las PQRS mediante palabras clave.

Los resultados posibles son:

* Positivo
* Negativo
* Neutral

Esta implementación corresponde a una solución básica y puede ser reemplazada posteriormente por un modelo especializado de análisis de sentimiento que permita una clasificación más robusta y contextual.


## Chatbot

El chatbot utiliza la API de Hugging Face mediante el modelo:

openai/gpt-oss-120b:fastest

El sistema puede utilizar información relacionada con las PQRS del usuario como contexto para generar respuestas, especialmente cuando se proporciona un código de radicado.

En caso de que el servicio externo no esté disponible, se utiliza un mecanismo de respuesta local basado en palabras clave.

# Requisitos

Para ejecutar el proyecto localmente se requiere:

* Python 3.13 o compatible.
* Git.
* Conexión a Internet.
* Configuración de los servicios externos que se deseen utilizar.

Las dependencias de Python se encuentran definidas en:

requirements.txt

# Instalación local

## 1. Clonar el repositorio

git clone https://github.com/Aress007/pqrs-inteligente.git
cd pqrs-inteligente

## 2. Crear un entorno virtual

### Windows

python -m venv venv
venv\Scripts\activate

### Linux o macOS

python3 -m venv venv
source venv/bin/activate

## 3. Instalar las dependencias

pip install -r requirements.txt

## 4. Configurar las variables de entorno

Crear un archivo `.env` en la raíz del proyecto.

Variables principales:

SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=
HF_TOKEN=
SENDGRID_API_KEY=
DEFAULT_FROM_EMAIL=
SITE_URL=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
EPAYCO_PUBLIC_KEY=
EPAYCO_PRIVATE_KEY=
EPAYCO_P_KEY=
EPAYCO_P_CUST_ID_CLIENTE=
EPAYCO_TEST=True

### Importante

El archivo `.env` contiene información sensible y **no debe publicarse en el repositorio**.

Las credenciales deben mantenerse fuera del código fuente y configurarse mediante variables de entorno.

## 5. Ejecutar las migraciones

python manage.py migrate

## 6. Crear un superusuario

Opcionalmente:

python manage.py createsuperuser

## 7. Ejecutar el servidor

python manage.py runserver

La aplicación estará disponible normalmente en:

http://127.0.0.1:8000/

# Variables de entorno

| Variable                   | Propósito                                |
| -------------------------- | ---------------------------------------- |
| `SECRET_KEY`               | Clave secreta de Django                  |
| `DEBUG`                    | Activa o desactiva el modo de depuración |
| `ALLOWED_HOSTS`            | Hosts permitidos por Django              |
| `HF_TOKEN`                 | Token de acceso a Hugging Face           |
| `SENDGRID_API_KEY`         | Clave de API de SendGrid                 |
| `DEFAULT_FROM_EMAIL`       | Correo utilizado como remitente          |
| `SITE_URL`                 | URL base de la aplicación                |
| `CLOUDINARY_CLOUD_NAME`    | Nombre de la cuenta de Cloudinary        |
| `CLOUDINARY_API_KEY`       | API Key de Cloudinary                    |
| `CLOUDINARY_API_SECRET`    | API Secret de Cloudinary                 |
| `EPAYCO_PUBLIC_KEY`        | Clave pública de ePayco                  |
| `EPAYCO_PRIVATE_KEY`       | Clave privada de ePayco                  |
| `EPAYCO_P_KEY`             | Clave P de ePayco                        |
| `EPAYCO_P_CUST_ID_CLIENTE` | Identificador del cliente en ePayco      |
| `EPAYCO_TEST`              | Define el uso del ambiente sandbox       |

# Estructura del proyecto

pqrs-inteligente/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/
│   ├── views.py
│   ├── urls.py
│   └── templates/
│
├── empresas/
│   ├── models.py
│   └── admin.py
│
├── pqrs/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── classification_service.py
│   ├── ia_service.py
│   └── templates/
│
├── usuarios/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── templates/
│
├── templates/
├── media/
├── staticfiles/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md

# Base de datos

Actualmente el proyecto utiliza **SQLite** mediante el archivo:

db.sqlite3

SQLite se utiliza para facilitar el despliegue, las pruebas y la demostración del proyecto.

Debido a las limitaciones de SQLite en escenarios de mayor concurrencia y escalabilidad, para una futura versión orientada a producción comercial se plantea la migración a **PostgreSQL** u otro sistema gestor de bases de datos en la nube.

# Despliegue

La aplicación se encuentra desplegada en:

**Render – Free Tier**

### Build Command

pip install -r requirements.txt && python manage.py collectstatic --noinput

### Start Command

gunicorn config.wsgi:application

### Servicios utilizados

* **Render:** alojamiento de la aplicación.
* **SQLite:** base de datos actual.
* **Cloudinary:** almacenamiento de archivos e imágenes.
* **SendGrid:** envío de correos electrónicos.
* **Hugging Face:** servicios de Inteligencia Artificial.
* **ePayco:** pagos en ambiente sandbox.

### URL de la aplicación

https://pqrs-inteligente.onrender.com

### Consideraciones del despliegue

El proyecto se encuentra desplegado en el plan gratuito de Render con fines académicos, de demostración y validación funcional.

El entorno gratuito presenta limitaciones de recursos y disponibilidad que deben considerarse antes de utilizar la aplicación en un entorno comercial.

Asimismo, el uso actual de SQLite responde a las necesidades del proyecto académico. Para una solución comercial se recomienda utilizar PostgreSQL u otro motor de base de datos administrado.

# Seguridad

El proyecto implementa diferentes medidas de seguridad:

* Protección CSRF en formularios.
* Autenticación mediante el sistema de sesiones de Django.
* Restricción de acceso mediante `@login_required`.
* Control de permisos según el rol del usuario.
* Validación de información mediante formularios Django.
* Uso de variables de entorno para información sensible.
* Tokens de recuperación de contraseña con expiración.
* Control de acceso a archivos adjuntos.
* Separación de credenciales del código fuente.

# Funcionalidades principales

## Cliente

El usuario con rol de cliente puede:

* Registrarse.
* Iniciar sesión.
* Recuperar su contraseña.
* Crear PQRS.
* Consultar sus solicitudes.
* Consultar el detalle de una PQRS.
* Responder solicitudes cuando corresponda.
* Consultar el estado de sus solicitudes.
* Consultar el historial de trazabilidad.
* Utilizar el chatbot.
* Editar su perfil.
* Cambiar su contraseña.

## Empresa

El usuario con rol de empresa puede:

* Registrarse como empresa.
* Seleccionar un plan de suscripción.
* Consultar el dashboard.
* Administrar las PQRS recibidas.
* Filtrar y buscar solicitudes.
* Consultar el detalle de las PQRS.
* Responder PQRS.
* Cambiar estados.
* Consultar el historial de trazabilidad.
* Supervisar el SLA.
* Exportar información a CSV.
* Gestionar su perfil y logo.
* Realizar copias de seguridad.
* Restaurar información.
* Gestionar la suscripción mediante ePayco en ambiente sandbox.

# Estado del proyecto

**Proyecto final desarrollado y desplegado para demostración académica.**

El sistema se encuentra funcional con las características descritas en esta documentación.

La versión actual está orientada a fines académicos, de demostración y validación funcional.

# Mejoras futuras

Entre las principales mejoras previstas se encuentran:

* Configuración de SLA personalizados por empresa.
* Migración de SQLite a PostgreSQL.
* Asignación automática de PQRS por áreas o departamentos.
* Implementación de notificaciones en tiempo real mediante WebSockets.
* Desarrollo de una API REST para integraciones externas.
* Incorporación de un modelo especializado de análisis de sentimiento.
* Mejora y especialización del chatbot para el dominio de PQRS.

# Enlaces

### Aplicación desplegada

https://pqrs-inteligente.onrender.com

### Repositorio

https://github.com/Aress007/pqrs-inteligente

### Modelo Entidad-Relación

https://dbdiagram.io/d/PQRS-INTELIGENTE-68af2626777b52b76cd29b73

# Autor

JOSE LUIS QUINTERO NAVARRO

Proyecto final – Programa de Formación

Técnico en Programación de Software

SENA - 2026

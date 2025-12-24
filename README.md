# 🎵 BeatStat Backend

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat&logo=fastapi)
![Redis](https://img.shields.io/badge/Redis-7.0+-red?style=flat&logo=redis)
![Spotify API](https://img.shields.io/badge/Spotify-API-1DB954?style=flat&logo=spotify)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)
[![GitHub](https://img.shields.io/badge/GitHub-nowhereOnce-black?style=flat&logo=github)](https://github.com/nowhereOnce)

Un backend construido con **FastAPI** que integra **Spotify OAuth 2.0** para mostrar estadísticas personalizadas de tu actividad musical. Obtén tus canciones más escuchadas, playlists y datos detallados de tu perfil de Spotify.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#configuración)
- [Uso](#-uso)
- [Endpoints](#-endpoints)
- [Flujo de Autenticación](#flujo-de-autenticación-detallado)
- [Variables de Entorno](#-variables-de-entorno)
- [Despliegue en Producción](#-despliegue-en-producción)

---

## ✨ Características

- ✅ **Autenticación OAuth 2.0 con Spotify** - Login seguro sin almacenar credenciales
- ✅ **Gestión de Sesiones con Redis** - Sesiones persistentes con expiración automática
- ✅ **Refresco Automático de Tokens** - Los tokens de Spotify se renuevan automáticamente
- ✅ **CORS Configurado** - Desarrollo y producción con dominios específicos
- ✅ **API RESTful** - Endpoints bien documentados y tipados
- ✅ **Manejo de Errores** - Excepciones HTTP apropiadas
- ✅ **Logging** - Debug y monitoreo de operaciones

---

## Arquitectura

```plaintext
BeatStat-backend
├── app/
│   ├── __init__.py          # Configuración inicial de la app
│   ├── main.py              # Puntos de entrada (login, callback, logout)
│   ├── dependencies.py      # Servicios reutilizables (Redis, Spotify, auth)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── routes.py        # Endpoints para obtener datos de Spotify
│   └── utils/
│       ├── __init__.py
│       └── spotify.py       # Utilidades para Spotify API
├── requirements.txt         # Dependencias del proyecto
├── .gitignore              # Archivos a ignorar en Git
└── README.md               # Este archivo
```

### Flujo de Datos

```plaintext
Usuario
   ↓
[/login] ────→ Spotify OAuth
   ↓
[/callback] ──→ Intercambio de código por token
   ↓
[Redis] ──────→ Almacenamiento de sesión (24h)
   ↓
[Cookie] ─────→ session_token enviada al cliente
   ↓
[/status] ────→ Validación de sesión
   ↓
[/me/top-tracks] → Obtención de datos personalizados
```

---

## 📋 Requisitos Previos

- **Python 3.8+**
- **Redis** (local o en la nube)
- **Cuenta de Spotify** (gratuita)
- **Aplicación registrada en Spotify Developer Dashboard**

---

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/BeatStat-back.git
cd BeatStat-back
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Redis

- **Opción A: Redis Local**

```bash
# En Ubuntu/Debian
sudo apt-get install redis-server
redis-server

# En macOS
brew install redis
redis-server
```

- **Opción B: Docker**

```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

- **Opción C: Redis Cloud (Producción)**

```plaintext
Registrarse en https://redis.com/try-free/
Obtener URL: redis://default:PASSWORD@HOST:PORT
```

---

## Configuración

### 1. Obtener Credenciales de Spotify

1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Inicia sesión o crea una cuenta
3. Haz clic en "Create an App"
4. Acepta los términos y crea la aplicación
5. En la página de la app, copia:
   - **Client ID**
   - **Client Secret**
6. En "Edit Settings", agrega los **Redirect URIs**:

   ```plaintext
   http://localhost:8000/callback        (desarrollo)
   https://app.beatstat.com/callback     (producción)
   ```

### 2. Crear Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Spotify OAuth
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
SPOTIFY_REDIRECT_URI=http://localhost:8000/callback

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
# O para Redis Cloud:
# REDIS_URL=redis://default:PASSWORD@HOST:PORT

# Aplicación
ENVIRONMENT=development
DEFAULT_REDIRECT_ENDPOINT=http://localhost:8000/status
```

**⚠️ IMPORTANTE:** Nunca subas el archivo `.env` a Git (está en `.gitignore`)

---

## 📖 Uso

### Iniciar el Servidor

```bash
python -m uvicorn app.main:app --reload --port 8000
```

La API estará disponible en: `http://localhost:8000`

### Documentación Interactiva

FastAPI genera documentación automática:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔌 Endpoints

### Autenticación

| Método | Endpoint | Descripción |
| -------- | ---------- | ------------- |
| `GET` | `/login` | Inicia flujo OAuth con Spotify |
| `GET` | `/callback` | Callback después de autenticación |
| `POST` | `/logout` | Cierra sesión y elimina cookie |
| `GET` | `/status` | Obtiene estado de sesión actual |

### Datos de Usuario

| Método | Endpoint | Descripción | Autenticación |
| -------- | ---------- | ------------- | ---------------- |
| `GET` | `/me/top-tracks` | Top 10 canciones más escuchadas | ✅ Requerida |
| `GET` | `/me/playlists` | Lista de playlists del usuario | ✅ Requerida |

### Salud

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Health check |

---

## Flujo de Autenticación Detallado

### 1. Usuario Inicia Login

```plaintext
GET /login
  ↓
Redirige a: https://accounts.spotify.com/authorize?client_id=...&redirect_uri=...
```

### 2. Usuario Autoriza en Spotify

```plaintext
Usuario ve: "BeatStat quiere acceso a tus datos"
            [Aceptar] [Denegar]
  ↓
Spotify redirige a: http://localhost:8000/callback?code=XXXXX
```

### 3. Backend Intercambia Código por Token

```plaintext
POST https://accounts.spotify.com/api/token
  client_id: XXXXX
  client_secret: XXXXX
  code: XXXXX
  ↓
Respuesta: {
  "access_token": "BEARER_TOKEN",
  "refresh_token": "REFRESH_TOKEN",
  "expires_in": 3600
}
```

### 4. Backend Guarda Sesión en Redis

```plaintext
redis.setex(
  key: "session:UUID",
  ttl: 86400 segundos (24 horas),
  value: {
    "token_info": {...},
    "user_info": {...},
    "created_at": "2024-01-01T12:00:00"
  }
)
```

### 5. Backend Devuelve Cookie de Sesión

```plaintext
Set-Cookie: session_token=UUID; Max-Age=86400; HttpOnly; Secure; SameSite=Lax
Redirect: http://localhost:8000/status
```

### 6. Cliente Usa Cookie en Peticiones Posteriores

```plaintext
GET /me/top-tracks
  Cookie: session_token=UUID
  ↓
Backend recupera sesión de Redis
Backend valida token de Spotify (refresca si es necesario)
Devuelve datos del usuario
```

---

## 🔧 Variables de Entorno

### Spotify OAuth

| Variable | Descripción | Ejemplo |
| ---------- | ------------- | --------- |
| `SPOTIFY_CLIENT_ID` | Client ID de Spotify | `abc123xyz...` |
| `SPOTIFY_CLIENT_SECRET` | Client Secret de Spotify | `secret123...` |
| `SPOTIFY_REDIRECT_URI` | URI donde Spotify redirige después de autorizar | `http://localhost:8000/callback` |

### Redis

| Variable | Descripción | Ejemplo | Predeterminado |
| ---------- | ------------- | --------- | ---------------- |
| `REDIS_HOST` | Host de Redis | `localhost` | `localhost` |
| `REDIS_PORT` | Puerto de Redis | `6379` | `6379` |
| `REDIS_PASSWORD` | Contraseña de Redis (opcional) | `mypassword` | `` |
| `REDIS_DB` | Base de datos de Redis | `0` | `0` |
| `REDIS_URL` | URL de Redis (alternativa) | `redis://default:pass@host:6379` | - |

### Aplicación

| Variable | Descripción | Valores | Predeterminado |
| ---------- | ------------- | -------- | ---------------- |
| `ENVIRONMENT` | Entorno de ejecución | `development`, `production` | `development` |
| `DEFAULT_REDIRECT_ENDPOINT` | URL a la que redirigir después de login | `http://localhost:8000/status` | `http://localhost:8000/status` |

---

## 🚢 Despliegue en Producción

### Cambios Necesarios

#### 1. Actualizar `.env`

```bash
ENVIRONMENT=production
SPOTIFY_REDIRECT_URI=https://app.beatstat.com/callback
DEFAULT_REDIRECT_ENDPOINT=https://app.beatstat.com/dashboard
REDIS_URL=redis://default:PASSWORD@redis-host.com:6379
```

#### 2. Usar Servidor ASGI (Gunicorn + Uvicorn)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

#### 3. Configurar CORS Correcto

En `main.py`, los dominios en producción están configurados:

```python
origins = [
    "https://app.beatstat.com",
    "https://www.app.beatstat.com",
]
```

#### 4. Usar HTTPS

Las cookies se configuran automáticamente en `secure=True` cuando `ENVIRONMENT=production`.

#### 5. Render

Actualmente este proyecto se encuentra desplegado en [Redis](https://dashboard.render.com/). Esto debido a que esta plataforma brinda una forma sencilla de despliegue en coordinación directa con operaciones Push del repositorio.

---

## 📚 Estructura de Archivos Importante

### `app/__init__.py`

Configuración inicial, constantes globales

### `app/main.py`

- Endpoints de autenticación: `/login`, `/callback`, `/logout`, `/status`
- Configuración de CORS
- Middleware

### `app/dependencies.py`

- Cliente Redis para gestionar sesiones
- Cliente OAuth de Spotify
- Funciones de validación de sesión
- Refresco automático de tokens

### `app/routes/routes.py`

- `/me/top-tracks` - Canciones más escuchadas
- `/me/playlists` - Playlists del usuario

### `app/utils/spotify.py`

- Funciones auxiliares para Spotify API

---

## 🐛 Solución de Problemas

### "Invalid client" error en `/callback`

- **Causa:** Client ID o Client Secret incorrecto  
- **Solución:** Verifica las credenciales en `.env` y en Spotify Dashboard

### "Connection refused" en Redis

- **Causa:** Redis no está corriendo
- **Solución:**

```bash
# Verifica si Redis está corriendo
redis-cli ping  # Debería devolver PONG
# Si no, inicia Redis
redis-server
```

### "Session not found" en `/me/top-tracks`

- **Causa:** Cookie `session_token` expirada o no enviada  
- **Solución:**  
    - Asegúrate de que el navegador acepta cookies
    - Intenta hacer login nuevamente
    - Verifica que `REDIS_HOST` y `REDIS_PORT` sean correctos

### CORS error en frontend

- **Causa:** Dominio del frontend no está en la lista de `origins`  
- **Solución:** Agrega tu dominio a `app.add_middleware(CORSMiddleware, allow_origins=[...])`

---

## 🔒 Seguridad

### Buenas Prácticas Implementadas

- ✅ **Cookies HttpOnly** - Imposible acceder vía JavaScript
- ✅ **Tokens de Sesión Aleatorios** - UUID v4 para cada sesión
- ✅ **Expiración Automática** - 24 horas en Redis
- ✅ **SameSite=Lax** - Protección contra CSRF
- ✅ **Secure Flag en Producción** - Solo HTTPS
- ✅ **No almacena credenciales** - Solo tokens de Spotify

---

## 👨‍💻 Autor

**Aguilar Ramos Enrique Alejandro** - [GitHub](https://github.com/nowhereOnce)

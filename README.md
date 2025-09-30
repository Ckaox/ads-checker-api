# Simplified Ads Checker API

A clean and focused FastAPI service for checking active advertisements across Meta (Facebook) and Google platforms. This API provides essential functionality for competitor analysis and market research.

## Features

- **Single Endpoint**: One simple endpoint for all functionality
- **Identity Resolution**: Automatically resolve domain ↔ Facebook page relationships  
- **Ads Detection**: Boolean detection of active ads on Meta and Google
- **Clean Response**: Simple, structured JSON responses
- **Production Ready**: Docker support, caching, and comprehensive error handling

## API Endpoint

### Check Ads
```http
POST /v1/check
```
Resolves identities and detects active ads in one call.

**Request (provide domain, Facebook page, or both):**
```json
{
  "domain": "nike.com",
  "facebook_page": "https://www.facebook.com/nike"
}
```

**Response:**
```json
{
  "domain": "nike.com",
  "facebook_page": "https://www.facebook.com/nike", 
  "meta_page_id": "15087023681",
  "has_meta_ads": true,
  "has_google_ads": true,
  "success": true,
  "message": "Resolved both domain and Facebook page. Active ads found: Meta ads detected, Google ads detected"
}
```

### Input Options
- **Domain only**: `{"domain": "example.com"}` → Finds Facebook page + checks ads
- **Facebook only**: `{"facebook_page": "https://facebook.com/page"}` → Finds domain + checks ads  
- **Both**: `{"domain": "example.com", "facebook_page": "https://facebook.com/page"}` → Validates + checks ads

## Installation and Usage

### Requirements
- Python 3.11+
- pip

### Instalación Local

1. **Clonar el repositorio:**
```bash
git clone <repository-url>
cd ads-checker
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar la aplicación:**
```bash
python main.py
```

La API estará disponible en `http://localhost:8000`

### Configuración

Crea un archivo `.env` basado en `.env.example`:

```env
# Meta/Facebook API Configuration (opcional)
META_ACCESS_TOKEN=your_meta_access_token_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Cache TTL in seconds
CACHE_TTL=3600
```

### Token de Meta (Opcional)

Para mejores resultados con Meta Ads, obtén un token de acceso:

1. Ve a [Facebook Developers](https://developers.facebook.com/)
2. Crea una aplicación
3. Genera un token con permisos `ads_read`
4. Agrega el token a tu archivo `.env`

**Nota:** La API funciona sin token usando scraping como fallback.

## Documentación de la API

Una vez ejecutando, visita:
- **Documentación interactiva**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health check**: `http://localhost:8000/health`

## Arquitectura

```
app/
├── api/v1/           # Endpoints de la API
├── core/             # Configuración y dependencias
├── providers/        # Clientes para Meta y Google
├── resolvers/        # Resolución dominio ↔ Facebook
├── schemas/          # Modelos Pydantic
└── services/         # Lógica de negocio
```

## Integración con Plataformas

### Meta (Facebook/Instagram)
- **API oficial**: Meta Ad Library API (requiere token)
- **Fallback**: Scraping de adslibrary.facebook.com
- **Características**: Detección precisa, metadatos completos

### Google Ads
- **Método principal**: Google Ads Transparency Center (scraping)
- **Método secundario**: Análisis de señales en el sitio web
- **Limitaciones**: No hay API pública, depende de scraping

## Deployment en Render

### Preparación
1. Asegúrate de tener todos los archivos necesarios
2. Configura las variables de entorno en Render
3. Usa Python 3.11+ como runtime

### Variables de entorno en Render
```
META_ACCESS_TOKEN=tu_token_aqui
API_HOST=0.0.0.0
API_PORT=10000
DEBUG=false
CACHE_TTL=3600
```

### Comando de inicio
```
python main.py
```

## Limitaciones y Consideraciones

### Rate Limiting
- La API implementa cache para reducir llamadas externas
- Respeta los límites de las plataformas objetivo

### Precisión
- **Meta**: Alta precisión con token, moderada con scraping
- **Google**: Moderada precisión, depende de heurísticas

### Legalidad
- Usa APIs oficiales cuando están disponibles
- El scraping se realiza de forma responsable
- Respeta robots.txt y términos de servicio

## Desarrollo

### Estructura del Proyecto
- **FastAPI**: Framework web moderno y rápido
- **Pydantic**: Validación de datos y serialización
- **httpx**: Cliente HTTP asíncrono
- **selectolax**: Parser HTML eficiente
- **cachetools**: Cache en memoria con TTL

### Testing
```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

### Contribuir
1. Fork el repositorio
2. Crea una rama feature
3. Implementa cambios con tests
4. Envía un pull request

## Soporte

Para problemas o preguntas:
- Crea un issue en GitHub
- Revisa la documentación en `/docs`
- Verifica los logs de la aplicación

## Licencia

MIT License - ver archivo LICENSE para detalles.

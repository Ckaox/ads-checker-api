# Guía de Deployment en Render

Esta guía te ayudará a deployar la API Ads Checker en Render (plan gratuito).

## Preparación

### 1. Repositorio Git
Asegúrate de que tu código esté en un repositorio Git (GitHub, GitLab, etc.):

```bash
git init
git add .
git commit -m "Initial commit: Ads Checker API"
git remote add origin <tu-repositorio-url>
git push -u origin main
```

### 2. Archivos necesarios
Verifica que tengas estos archivos en tu repositorio:
- ✅ `requirements.txt` - Dependencias de Python
- ✅ `main.py` - Aplicación principal
- ✅ `render.yaml` - Configuración de Render
- ✅ `Dockerfile` - Para deployment con Docker (opcional)

## Deployment en Render

### Opción 1: Deployment Automático (Recomendado)

1. **Conectar repositorio:**
   - Ve a [render.com](https://render.com)
   - Crea una cuenta o inicia sesión
   - Conecta tu cuenta de GitHub/GitLab
   - Selecciona "New +" → "Web Service"
   - Conecta tu repositorio `ads-checker`

2. **Configuración automática:**
   - Render detectará automáticamente el `render.yaml`
   - Revisa la configuración generada
   - Haz clic en "Create Web Service"

### Opción 2: Configuración Manual

1. **Crear Web Service:**
   - En Render Dashboard: "New +" → "Web Service"
   - Conecta tu repositorio

2. **Configuración del servicio:**
   ```
   Name: ads-checker-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
   ```

3. **Variables de entorno:**
   ```
   API_HOST=0.0.0.0
   DEBUG=false
   CACHE_TTL=3600
   ```

   **Opcional (para mejor funcionalidad):**
   ```
   META_ACCESS_TOKEN=tu_token_de_meta_aqui
   ```

## Configuración de Variables de Entorno

### Variables Requeridas
- `API_HOST`: `0.0.0.0` (obligatorio para Render)
- `DEBUG`: `false` (para producción)
- `CACHE_TTL`: `3600` (1 hora de cache)

### Variables Opcionales
- `META_ACCESS_TOKEN`: Token de Meta para mejor precisión en detección de ads

### Cómo agregar variables en Render:
1. Ve a tu servicio en Render Dashboard
2. Pestaña "Environment"
3. Agrega las variables necesarias
4. Guarda cambios (triggerea un redeploy automático)

## Obtener Token de Meta (Opcional)

Para mejorar la precisión de detección de Meta Ads:

1. **Crear App de Facebook:**
   - Ve a [developers.facebook.com](https://developers.facebook.com)
   - Crea una nueva aplicación
   - Tipo: "Business" o "Consumer"

2. **Configurar permisos:**
   - Agrega el producto "Marketing API"
   - Solicita permisos: `ads_read`, `pages_read_engagement`

3. **Generar token:**
   - Ve a "Tools" → "Graph API Explorer"
   - Selecciona tu app
   - Genera token con permisos necesarios
   - Copia el token y agrégalo como variable de entorno

## Verificación del Deployment

### 1. Verificar que el servicio esté corriendo:
```bash
curl https://tu-app.onrender.com/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "service": "ads-checker-api",
  "version": "1.0.0"
}
```

### 2. Probar endpoint principal:
```bash
curl -X POST "https://tu-app.onrender.com/v1/check-presence" \
  -H "Content-Type: application/json" \
  -d '{"domain": "coca-cola.com"}'
```

### 3. Ver documentación:
- Swagger UI: `https://tu-app.onrender.com/docs`
- ReDoc: `https://tu-app.onrender.com/redoc`

## Monitoreo y Logs

### Ver logs en tiempo real:
1. Render Dashboard → Tu servicio
2. Pestaña "Logs"
3. Filtra por tipo de log (Build, Deploy, Runtime)

### Métricas básicas:
- CPU y memoria en pestaña "Metrics"
- Requests y respuestas en "Events"

## Limitaciones del Plan Gratuito

### Render Free Tier:
- **Recursos**: 512 MB RAM, 0.1 CPU
- **Sleep**: Servicio se "duerme" después de 15 min de inactividad
- **Tiempo de build**: Máximo 15 minutos
- **Bandwidth**: 100 GB/mes

### Consideraciones:
- **Cold starts**: Primera request después del sleep puede tardar 30+ segundos
- **Rate limiting**: Implementa cache agresivo para reducir requests externos
- **Timeouts**: Ajusta timeouts para requests externos (30s máximo recomendado)

## Troubleshooting

### Problemas Comunes:

1. **Build falla:**
   ```
   Error: No module named 'X'
   ```
   **Solución**: Verifica `requirements.txt` y versiones de dependencias

2. **Servicio no responde:**
   ```
   Error: Application failed to bind to $PORT
   ```
   **Solución**: Verifica que uses `os.environ.get("PORT")` en main.py

3. **Timeouts en requests externos:**
   ```
   Error: Request timeout
   ```
   **Solución**: Reduce `HTTP_TIMEOUT` a 20-30 segundos

4. **Memory issues:**
   ```
   Error: Process killed (OOM)
   ```
   **Solución**: Optimiza cache, reduce concurrencia de requests

### Logs útiles:
```bash
# Ver logs recientes
curl https://tu-app.onrender.com/health -v

# Verificar variables de entorno (en logs de startup)
grep "🚀 Ads Checker API starting up" logs
```

## Actualizaciones

### Auto-deployment:
- Render redeploya automáticamente en cada push a `main`
- Monitorea el progreso en Dashboard → "Events"

### Manual deployment:
- Dashboard → Tu servicio → "Manual Deploy" → "Deploy latest commit"

## Escalabilidad

### Para mayor tráfico, considera:
1. **Upgrade a plan pagado** ($7/mes para más recursos)
2. **Implementar Redis** para cache distribuido
3. **Rate limiting** más agresivo
4. **CDN** para responses estáticas

## Seguridad

### Buenas prácticas implementadas:
- ✅ Variables de entorno para secrets
- ✅ CORS configurado
- ✅ Timeouts en requests externos
- ✅ Validación de input con Pydantic
- ✅ Error handling robusto

### Recomendaciones adicionales:
- Considera agregar autenticación para uso en producción
- Implementa rate limiting por IP
- Monitorea logs para detectar abusos

## Soporte

### Recursos útiles:
- [Render Docs](https://render.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- Logs del servicio en Render Dashboard

### Contacto:
- Issues en el repositorio del proyecto
- Render Support (para problemas de plataforma)

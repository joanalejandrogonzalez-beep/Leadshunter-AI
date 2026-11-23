# LeadHunter AI — Plataforma SaaS Global de Prospección B2B

Plataforma SaaS multi-inquilino y multi-empresa con backend FastAPI y frontend Next.js para encontrar, analizar, calificar y organizar prospectos comerciales en cualquier país del mundo. Combina búsqueda geográfica internacional, enriquecimiento web ético y asistente conversacional de IA.

## Instalación y Ejecución en Windows
1. Instala **Python 3.10 o superior** desde python.org (marca *Add Python to PATH*).
2. Instala **Node.js LTS 20+** desde nodejs.org.
3. Clona o descomprime la carpeta `LeadHunter`.
4. Configuración de entorno: copia `.env.example` a `.env` si deseas personalizar variables (`JWT_SECRET_KEY`, `DATABASE_URL`, etc.).
5. Ejecutables rápidos:
   * **`run.bat`**: crea el entorno virtual `.venv`, instala dependencias de Python, inicia el backend FastAPI y luego arranca el frontend Next.js en `http://localhost:3000`.
   * **`run_api.bat`**: inicia solo el backend FastAPI en `http://127.0.0.1:8000` con documentación Swagger en `http://127.0.0.1:8000/docs`.
   * **`run_scheduled.bat`**: ejecuta las prospecciones programadas en segundo plano.

Ejecución manual por terminal:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```powershell
cd frontend
$env:PATH = "$env:LOCALAPPDATA\nodejs\node-v22.11.0-win-x64;$env:PATH"
npx next dev -H 0.0.0.0 -p 3000
```

## Uso
- **Acceso Next.js**: el registro e inicio de sesión de la interfaz Next.js usan FastAPI; el token se guarda en una cookie `HttpOnly` y no se expone a JavaScript del navegador. La opción “Recordarme” extiende la sesión a 30 días. En producción, publica siempre detrás de HTTPS.
- **Usuarios existentes**: al iniciar FastAPI, se copian a `leadhunter_v2.db` las cuentas de `leadhunter.db` que ya tengan contraseña bcrypt. No se asignan empresas antiguas automáticamente, porque la base anterior no guardaba la relación entre usuario y empresa.
- **Buscar**: país, ciudad, sector y fuentes. Guarda empresas sin duplicar (por dominio o nombre+ciudad) y, si lo activas, analiza cada web.
- **Leads**: filtra, abre un lead, mira el desglose del score, las evidencias, cambia estado, añade notas y fecha de seguimiento, genera el mensaje (ES/EN) y exporta CSV.
- **Importar CSV**: plan B si una fuente falla. Columnas: `name/nombre`, `website/web`, `phone/telefono`, `email/correo`, `instagram`, `city/ciudad`, `country/pais`, `sector`. Ver `sample_leads.csv`.
- **Programación**: guarda búsquedas y ejecútalas a mano (▶) o automáticamente.
- **Recordar sesión**: al iniciar sesión o registrarte, puedes marcar “Recordarme en este dispositivo durante 30 días”. La sesión se puede revocar al cerrar sesión y en la base solo se guarda el digest del token. La librería de cookies usada por Streamlit no permite marcarla `HttpOnly`; para datos sensibles, publica solo sobre HTTPS y prefiere autenticación OIDC (`st.login`) antes de exponer la app a Internet.

## Fuentes gratuitas
| Fuente | Qué aporta | Limitaciones |
|---|---|---|
| Serper.dev | Resultados orgánicos de Google para consultas B2B | Requiere `SERPER_API_KEY` |
| Tavily | Resultados web con extractos de páginas | Requiere `TAVILY_API_KEY` |
| OpenStreetMap (Nominatim + Overpass) | Empresas con etiquetas públicas (nombre, web, teléfono…) | En República Dominicana la cobertura es parcial |
| DuckDuckGo (HTML) | Descubre webs corporativas | Puede bloquear si abusas; la app hace pocas consultas con pausas |
| Tu CSV | Lo que tú ya tengas | — |

El motor agéntico usa Serper si hay clave; si no, Tavily y luego DuckDuckGo. OpenStreetMap complementa resultados cuando hacen falta más candidatos. Para activar un proveedor, copia `.env.example` a `.env` y configura `SERPER_API_KEY` o `TAVILY_API_KEY`; `GEMINI_API_KEY` es opcional para interpretar solicitudes y responder preguntas generales. Sin esas claves se usan búsqueda gratuita y reglas locales.

La app **respeta `robots.txt`**, lee como máximo 3 páginas por web con timeout y usa un User-Agent identificado. No scrapea Instagram, Google Maps ni LinkedIn; solo extrae los enlaces públicos de Instagram o LinkedIn que la propia web de la empresa publica.

## Cómo se puntúa (0-100)
Encaje 30 · Capacidad económica **estimada** 20 · Necesidad 25 · Actividad 15 · Calidad de datos 10. Cada lead muestra:
- ✅ **Evidencias verificadas**: lo observado en la web o en la fuente (p. ej. “no se detectó vídeo”, “copyright 2019”).
- 🔶 **Inferencias**: interpretaciones (p. ej. “muchos proyectos → operación de volumen”). La capacidad de invertir RD$50,000+ nunca se da por hecha.

El score es una guía para priorizar, no un veredicto: revisa siempre la web antes de contactar. “No se detectó” significa que no aparece en las páginas leídas, no que no exista.

## Mensajes
Plantillas gratuitas (sin IA externa) que usan solo evidencias observadas como gancho. **Nada se envía automáticamente**: copias el borrador, lo ajustas y contactas tú.

## Búsquedas programadas (Windows)
1. Guarda búsquedas en *Buscar → Guardar búsqueda*.
2. Abre el **Programador de tareas** → *Crear tarea básica* → frecuencia semanal → acción *Iniciar un programa* → elige `run_scheduled.bat`.
3. Resultados en la app y registro en `data\scheduled.log`.

## Publicar en un repositorio público
- Las claves opcionales de búsqueda/LLM se guardan en `.env`, que está excluido de Git; nunca las escribas en el código.
- El `.gitignore` incluido excluye `data/` (tu base de datos con leads, notas y contactos), logs, `.env`, `.venv` y cualquier `*.csv` salvo `sample_leads.csv`. **Tus prospectos nunca deben subirse.**
- Antes del primer commit: `git status` y comprueba que no aparezca nada de `data/` ni CSV propios.

## Datos y pruebas
- Base de datos relacional multi-tenant: `data\leadhunter_v2.db` (PostgreSQL en producción vía `DATABASE_URL`).
- Base de datos SQLite local: `data\leadhunter.db`.
- Suite de pruebas completa:
  * `python test_smoke.py`: prueba offline del motor de scraping, análisis y scoring.
  * `python test_prospecting.py`: prueba offline de intención, descubrimiento, calificación, outreach y contrato de chat.
  * `python test_saas_security.py`: verificación de aislamiento multi-tenant, hashing bcrypt y prevención de IDOR.
  * `python test_api.py`: pruebas funcionales de endpoints HTTP, tokens JWT y pipeline conversacional.

## Estructura
`frontend/` interfaz Next.js (migración gradual desde Streamlit) · `app.py` interfaz Streamlit existente · `backend/main.py` API FastAPI para Next.js · `leadhunter/prospecting.py` herramientas y orquestación · `leadhunter/sources.py` fuentes · `leadhunter/analyzer.py` análisis web · `leadhunter/scoring.py` puntuación · `leadhunter/messages.py` outreach.

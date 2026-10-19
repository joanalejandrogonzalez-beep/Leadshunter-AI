[README.md](https://github.com/user-attachments/files/33684659/README.md)
# LeadHunter AI

Aplicación local (Python + Streamlit + SQLite) para encontrar, investigar y clasificar leads de **Novus Ops** y **NTO Productions**. Sin APIs de pago ni claves. Los dos negocios están completamente separados: se elige en la barra lateral y cada lista, dashboard y exportación solo muestra su negocio.

## Instalación en Windows
1. Instala **Python 3.10 o superior** desde python.org (marca *Add Python to PATH*).
2. Descomprime la carpeta `LeadHunter`.
3. Haz doble clic en **`run.bat`**. La primera vez crea el entorno e instala dependencias; después abre la app en tu navegador (http://localhost:8501).

Manual: `python -m venv .venv`, `.venv\Scripts\activate`, `pip install -r requirements.txt`, `streamlit run app.py`.

## Uso
- **Buscar**: país, ciudad, sector y fuentes. Guarda empresas sin duplicar (por dominio o nombre+ciudad) y, si lo activas, analiza cada web.
- **Leads**: filtra, abre un lead, mira el desglose del score, las evidencias, cambia estado, añade notas y fecha de seguimiento, genera el mensaje (ES/EN) y exporta CSV.
- **Importar CSV**: plan B si una fuente falla. Columnas: `name/nombre`, `website/web`, `phone/telefono`, `email/correo`, `instagram`, `city/ciudad`, `country/pais`, `sector`. Ver `sample_leads.csv`.
- **Programación**: guarda búsquedas y ejecútalas a mano (▶) o automáticamente.

## Fuentes gratuitas
| Fuente | Qué aporta | Limitaciones |
|---|---|---|
| OpenStreetMap (Nominatim + Overpass) | Empresas con etiquetas públicas (nombre, web, teléfono…) | En República Dominicana la cobertura es parcial |
| DuckDuckGo (HTML) | Descubre webs corporativas | Puede bloquear si abusas; la app hace pocas consultas con pausas |
| Tu CSV | Lo que tú ya tengas | — |

La app **respeta `robots.txt`**, lee como máximo 4 páginas por web con pausa de 1 s y usa un User-Agent identificado. No usa Instagram, Google Maps ni LinkedIn (sus condiciones prohíben el scraping); solo guarda el enlace de Instagram si la propia web de la empresa o OSM lo publican.

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
- La app **no usa ninguna clave de API ni credenciales**; no hay nada secreto en el código.
- El `.gitignore` incluido excluye `data/` (tu base de datos con leads, notas y contactos), logs, `.env`, `.venv` y cualquier `*.csv` salvo `sample_leads.csv`. **Tus prospectos nunca deben subirse.**
- Antes del primer commit: `git status` y comprueba que no aparezca nada de `data/` ni CSV propios.

## Datos y pruebas
- Base de datos: `data\leadhunter.db` (haz copia de este archivo para respaldar).
- Prueba sin internet: `python test_smoke.py`.

## Estructura
`app.py` interfaz · `assets/logo.svg` logo · `leadhunter/db.py` datos · `sources.py` fuentes · `analyzer.py` análisis web · `scoring.py` puntuación · `messages.py` plantillas · `pipeline.py` flujo.

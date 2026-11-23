# LeadHunter AI — Frontend (Next.js + Tailwind CSS)

Landing page y Hero Section de alta fidelidad diseñada según el **Manual de Identidad y Paleta de Colores Corporativa** de LeadHunter AI.

---

## 🎨 Sistema de Diseño y Tokens
- **Fondo Base (Obsidian Black):** `#050B14`
- **Superficies & Tarjetas (Deep Navy):** `#0B1329`
- **Acento Primario (Electric Blue):** `#0055FF`
- **Destellos & Acentos:** Cyan `#38BDF8` y Neon `#00E5BE`
- **Texto Principal:** Pure White `#FFFFFF` (WCAG AAA)
- **Texto Secundario:** Slate Gray `#94A3B8`
- **Glassmorphism:** `backdrop-blur-md bg-brand-navy/60 border border-white/10`

---

## 🏗️ Estructura de Componentes

```text
src/
├── app/
│   ├── layout.tsx                  # Tipografías Plus Jakarta Sans / Outfit y metadatos SEO
│   ├── page.tsx                    # Landing Page ensamble (Navbar + Mesh + HeroSection)
│   └── globals.css                 # Utilidades Glassmorphism y gradientes webkit
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx              # Header sticky, isotipo oficial, enlaces y CTAs
│   │   └── BackgroundMesh.tsx      # Mesh gradient oscuro ambiental + retícula radar
│   ├── hero/
│   │   ├── HeroSection.tsx         # Orquestador del Hero
│   │   ├── HeroBadge.tsx           # Pill badge "⚡ Prospección B2B impulsada por IA explicable"
│   │   ├── HeroHeadline.tsx        # H1 con gradiente dual y subtítulo en Slate Gray
│   │   └── SearchBarCTA.tsx        # Input de búsqueda interactiva con filtrado en tiempo real
│   └── preview/
│       ├── DashboardMockup.tsx     # Tarjeta flotante con efecto 3D tilt
│       ├── MockupHeader.tsx        # Cabecera de pipeline y badge de leads verificados
│       ├── ProspectRow.tsx         # Fila de lead con isotipo de verificación y etapas CRM
│       └── MatchScoreBadge.tsx     # Indicador de Match Score en verde/azul neón
└── data/
    └── mockProspects.ts            # Datos simulados de prospectos con señales auditadas
```

---

## 🚀 Cómo Ejecutar en Local

Cuando instales Node.js en tu máquina o despliegues en Vercel:

```bash
cd frontend
npm install
npm run dev
```

Abre en tu navegador: `http://localhost:3000`

---

## 👁️ Preview Inmediato sin Node.js
También tienes disponible el archivo interactivo independiente:
- `landing_preview.html` en la raíz del proyecto.

export interface Prospect {
  id: string;
  name: string;
  website: string;
  city: string;
  country: string;
  sector: string;
  matchScore: number;
  signals: string[];
  crmStage: "Frío" | "Templado" | "Caliente";
  verified: boolean;
}

export const MOCK_PROSPECTS: Prospect[] = [
  {
    id: "lead-1",
    name: "Constructora del Este SRL",
    website: "constructoraeste.com.do",
    city: "Santo Domingo",
    country: "República Dominicana",
    sector: "Construcción & Bienes Raíces",
    matchScore: 96,
    signals: ["Sin optimización móvil", "Catálogo sin descarga", "Presupuesto alto"],
    crmStage: "Caliente",
    verified: true,
  },
  {
    id: "lead-2",
    name: "Clínica Dental OdontoAdvanced",
    website: "odontoadvanced.com.do",
    city: "Santo Domingo",
    country: "República Dominicana",
    sector: "Salud & Especialidades",
    matchScore: 91,
    signals: ["Falta botón directo WhatsApp", "Pixel de Meta ausente"],
    crmStage: "Templado",
    verified: true,
  },
  {
    id: "lead-3",
    name: "Grupo Inmobiliario Las Américas",
    website: "inmobiliarialasamericas.do",
    city: "Santo Domingo",
    country: "República Dominicana",
    sector: "Desarrollos Inmobiliarios",
    matchScore: 88,
    signals: ["Carga lenta (>4.2s)", "Sin cotizador dinámico"],
    crmStage: "Caliente",
    verified: true,
  },
  {
    id: "lead-4",
    name: "Consultores Financieros Alfa",
    website: "alfaconsultoria.com",
    city: "Santo Domingo",
    country: "República Dominicana",
    sector: "Legal & Corporativo",
    matchScore: 78,
    signals: ["Presencia web mínima", "Excelente reputación local"],
    crmStage: "Frío",
    verified: true,
  },
  {
    id: "lead-5",
    name: "Arquitectura & Proyectos Caribe",
    website: "caribearquitectura.do",
    city: "Santo Domingo",
    country: "República Dominicana",
    sector: "Diseño & Construcción",
    matchScore: 84,
    signals: ["Sin certificado SSL", "Fotos de portafolio pesadas"],
    crmStage: "Templado",
    verified: true,
  },
];

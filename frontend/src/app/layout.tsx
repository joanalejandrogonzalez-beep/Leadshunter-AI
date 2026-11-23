import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Outfit } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "LeadHunter AI — Prospección B2B Inteligente y Explicable",
  description: "Encuentra y califica prospectos B2B en segundos. Auditoría web de señales comerciales, puntuación de afinidad y exportación directa a tu CRM.",
  icons: {
    icon: "/isotipo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${jakarta.variable} ${outfit.variable}`}>
      <body className="bg-[#f3f4f6] text-slate-900 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}

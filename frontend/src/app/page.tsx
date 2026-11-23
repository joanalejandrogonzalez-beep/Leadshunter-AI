"use client";

import { FormEvent, useEffect, useState } from "react";

const starterPrompts = [
  "¿En qué puedo ayudarte?",
  "Busca empresas en Madrid",
  "Analiza mi nicho B2B",
  "Encuentra prospectos en Santo Domingo",
];

type Prospect = {
  name: string;
  website?: string;
  email?: string;
  phone?: string;
  linkedin?: string;
  instagram?: string;
  score: number;
  diagnosis: string;
  outreach: string;
};

type SessionUser = {
  id: string;
  email: string;
  full_name: string;
};

export default function HomePage() {
  const [authStatus, setAuthStatus] = useState<"loading" | "signed_out" | "signed_in">("loading");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [user, setUser] = useState<SessionUser | null>(null);
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const [leads, setLeads] = useState<Prospect[]>([]);
  const [searchErrors, setSearchErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [hashText, setHashText] = useState("");
  const [hashValue, setHashValue] = useState<string | null>(null);
  const [hashLoading, setHashLoading] = useState(false);

  useEffect(() => {
    fetch("/api/auth/session", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) {
          setAuthStatus("signed_out");
          return;
        }
        const data = await response.json();
        setUser(data.user);
        setAuthStatus("signed_in");
      })
      .catch(() => setAuthStatus("signed_out"));
  }, []);

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError(null);

    try {
      const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const payload = authMode === "login"
        ? { email, password, remember_me: rememberMe }
        : {
            email,
            password,
            full_name: fullName,
            organization_name: organizationName,
            remember_me: rememberMe,
          };
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "No se pudo completar el acceso.");
      }

      setUser(data.user);
      setAuthStatus("signed_in");
      setPassword("");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "No se pudo completar el acceso.");
    } finally {
      setAuthLoading(false);
    }
  };

  const signOut = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
    setAuthStatus("signed_out");
    setMessage("");
    setReply(null);
    setLeads([]);
    setSearchErrors([]);
  };

  const sendPrompt = async (value?: string) => {
    const prompt = (value ?? message).trim();
    if (!prompt) return;

    setLoading(true);
    setReply(null);
    setLeads([]);
    setSearchErrors([]);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business: "LeadHunter", message: prompt }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "La búsqueda no pudo completarse.");
      setReply(data.reply || "Sin respuesta");
      setLeads(Array.isArray(data.leads) ? data.leads : []);
      setSearchErrors(Array.isArray(data.errors) ? data.errors : []);
    } catch (error) {
      setReply(error instanceof Error ? error.message : "No se pudo conectar con la API de LeadHunter.");
    } finally {
      setLoading(false);
      setMessage("");
    }
  };

  const downloadCsv = () => {
    const columns: (keyof Prospect)[] = [
      "name", "score", "website", "email", "phone", "linkedin", "instagram", "diagnosis", "outreach",
    ];
    const rows = [columns, ...leads.map((lead) => columns.map((column) => lead[column] ?? ""))];
    const csv = rows
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
      .join("\r\n");
    const fileUrl = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" }));
    const downloadLink = document.createElement("a");
    downloadLink.href = fileUrl;
    downloadLink.download = "leadhunter_prospectos.csv";
    downloadLink.click();
    URL.revokeObjectURL(fileUrl);
  };

  const hashWithBlake2b = async () => {
    const text = hashText.trim();
    if (!text) return;

    setHashLoading(true);
    setHashValue(null);

    try {
      const response = await fetch("http://localhost:8000/api/hash/blake2b", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "No se pudo generar el hash.");

      setHashValue(data.digest || "");
    } catch (error) {
      setHashValue(error instanceof Error ? error.message : "Error al generar el hash.");
    } finally {
      setHashLoading(false);
    }
  };

  if (authStatus === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f3f4f6] text-sm text-slate-600">
        Verificando tu sesión...
      </main>
    );
  }

  if (authStatus === "signed_out") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#f3f4f6] px-4 py-10 text-slate-900">
        <section className="w-full max-w-[460px] rounded-[22px] border border-slate-200 bg-white/90 p-6 shadow-[0_18px_38px_rgba(15,23,42,0.08)] backdrop-blur-sm">
          <div className="mb-7 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-blue-200 bg-blue-50 text-2xl text-blue-600">✦</div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">LeadHunter AI</h1>
            <p className="mt-2 text-sm text-slate-500">Accede a tu espacio de prospección</p>
          </div>

          <div className="mb-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-sm">
            <button
              type="button"
              onClick={() => { setAuthMode("login"); setAuthError(null); }}
              className={`rounded-lg px-3 py-2 font-medium transition ${authMode === "login" ? "bg-white text-blue-700 shadow-sm" : "text-slate-600"}`}
            >
              Iniciar sesión
            </button>
            <button
              type="button"
              onClick={() => { setAuthMode("register"); setAuthError(null); }}
              className={`rounded-lg px-3 py-2 font-medium transition ${authMode === "register" ? "bg-white text-blue-700 shadow-sm" : "text-slate-600"}`}
            >
              Crear cuenta
            </button>
          </div>

          <form onSubmit={submitAuth} className="space-y-4">
            {authMode === "register" && (
              <>
                <label className="block text-sm font-medium text-slate-700">
                  Nombre completo
                  <input
                    required
                    minLength={1}
                    maxLength={255}
                    autoComplete="name"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Nombre de tu empresa
                  <input
                    required
                    minLength={1}
                    maxLength={255}
                    autoComplete="organization"
                    value={organizationName}
                    onChange={(event) => setOrganizationName(event.target.value)}
                    className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  />
                </label>
              </>
            )}

            <label className="block text-sm font-medium text-slate-700">
              Correo electrónico
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Contraseña
              <input
                required
                type="password"
                minLength={authMode === "register" ? 8 : 1}
                maxLength={128}
                autoComplete={authMode === "login" ? "current-password" : "new-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
              />
              {authMode === "register" && <span className="mt-1 block text-xs font-normal text-slate-500">Usa al menos 8 caracteres.</span>}
            </label>

            <label className="flex items-start gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(event) => setRememberMe(event.target.checked)}
                className="mt-0.5 accent-blue-600"
              />
              <span>Recordarme en este dispositivo durante 30 días</span>
            </label>

            {authError && (
              <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
                {authError}
              </div>
            )}

            <button
              type="submit"
              disabled={authLoading}
              className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {authLoading ? "Procesando..." : authMode === "login" ? "Ingresar a mi espacio" : "Crear cuenta y continuar"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f3f4f6] text-slate-900">
      <div className="flex min-h-screen">
        <aside className="hidden w-[270px] shrink-0 border-r border-slate-200 bg-[#f5f5f6] p-4 md:flex md:flex-col">
          <div className="mb-6 flex items-center gap-3 px-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-lg text-blue-600">L</div>
            <div className="text-sm font-semibold text-slate-700">LeadHunter</div>
          </div>

          <button className="mb-5 flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm">
            + Nuevo
          </button>

          <nav className="space-y-2 text-sm text-slate-700">
            <div className="rounded-xl bg-slate-100 px-3 py-2 font-medium">Buscar</div>
            <div className="rounded-xl px-3 py-2">Proyectos</div>
            <div className="rounded-xl px-3 py-2">Artefactos</div>
            <div className="rounded-xl px-3 py-2">Personalización</div>
          </nav>

          <div className="mt-8 border-t border-slate-200 pt-5">
            <div className="mb-3 px-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Chats</div>
            <ul className="space-y-2 text-sm text-slate-600">
              <li className="rounded-lg px-2 py-2">Práctica resuelta en archivo .do</li>
              <li className="rounded-lg px-2 py-2">Resolución de ejercicios</li>
              <li className="rounded-lg px-2 py-2">Guión real feria Banreservas</li>
            </ul>
          </div>
        </aside>

        <section className="flex flex-1 flex-col">
          <header className="flex items-center justify-end gap-3 px-6 py-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700">
              Plan Free · Mejorar plan
            </div>
            <button
              onClick={signOut}
              className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-blue-200 hover:text-blue-700"
            >
              Cerrar sesión
            </button>
          </header>

          <div className="flex flex-1 items-center justify-center px-6 pb-12 pt-10">
            <div className="w-full max-w-[900px]">
              <div className="mb-8 text-center">
                <div className="inline-flex items-center gap-4 text-[clamp(2.2rem,4vw,4rem)] font-bold tracking-[-0.06em] text-slate-900">
                  <span className="flex h-[54px] w-[54px] items-center justify-center rounded-2xl border border-blue-200 bg-blue-50 text-2xl text-blue-600">✦</span>
                  <span>Hola, {user?.full_name.trim().split(/\s+/)[0] || user?.email}</span>
                </div>
              </div>

              <div className="rounded-[22px] border border-slate-200 bg-white/85 p-4 shadow-[0_12px_30px_rgba(15,23,42,0.04)] backdrop-blur-sm">
                <div className="mb-4 text-left text-lg font-medium text-slate-700">¿En qué puedo ayudarte?</div>

                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <button className="flex h-8 w-8 items-center justify-center rounded-xl border border-blue-200 bg-blue-50 text-lg text-blue-600">＋</button>
                  <span className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">Chat</span>
                  <span className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">Cowork</span>
                  <span className="ml-auto text-sm text-slate-500">Sonnet 5.5 Medio</span>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {starterPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => sendPrompt(prompt)}
                      className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>

                <div className="mt-5 flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") sendPrompt();
                    }}
                    placeholder="Escribe tu consulta..."
                    className="flex-1 border-0 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
                  />
                  <button
                    onClick={() => sendPrompt()}
                    disabled={loading}
                    className="rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-2 text-sm font-medium text-white shadow-md transition hover:opacity-95 disabled:opacity-60"
                  >
                    {loading ? "Analizando..." : "Enviar"}
                  </button>
                </div>

                {loading && (
                  <div role="status" className="mt-4 flex items-center gap-3 rounded-xl border border-blue-900/70 bg-[#0A0F1D] px-4 py-3 text-xs text-blue-100">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300/30 border-t-blue-400" aria-hidden="true" />
                    Buscando empresas, analizando sitios y calificando prospectos...
                  </div>
                )}

                {reply && (
                  <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-slate-700 shadow-sm">
                    {reply}
                  </div>
                )}

                {searchErrors.length > 0 && (
                  <div role="status" className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                    Algunas fuentes no respondieron: {searchErrors.join("; ")}
                  </div>
                )}

                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-800">Hash Blake2b (integridad)</h3>
                    <span className="text-[11px] text-slate-500">No para contraseñas</span>
                  </div>

                  <div className="flex flex-col gap-3 md:flex-row">
                    <input
                      value={hashText}
                      onChange={(e) => setHashText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") hashWithBlake2b();
                      }}
                      placeholder="Escribe texto para hashear..."
                      className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-blue-300"
                    />
                    <button
                      onClick={hashWithBlake2b}
                      disabled={hashLoading || !hashText.trim()}
                      className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {hashLoading ? "Generando..." : "Generar hash"}
                    </button>
                  </div>

                  {hashValue && (
                    <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-3 text-xs text-slate-700 break-all">
                      <div className="mb-1 font-semibold text-slate-800">Digest Blake2b:</div>
                      {hashValue}
                    </div>
                  )}
                </div>

                {leads.length > 0 && (
                  <section className="mt-6 rounded-xl border border-blue-900/70 bg-[#0A0F1D] p-4" aria-label="Prospectos calificados">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                      <h2 className="text-sm font-semibold text-white">
                        {leads.length} prospectos calificados
                      </h2>
                      <button
                        onClick={downloadCsv}
                        className="inline-flex items-center gap-2 rounded-lg border border-blue-800 bg-[#1E40AF] px-3 py-2 text-xs font-medium text-white transition hover:border-blue-400 hover:bg-[#3B82F6]"
                      >
                        <span aria-hidden="true">↓</span> Descargar CSV
                      </button>
                    </div>
                    <div className="overflow-x-auto rounded-xl border border-blue-900/70 bg-[#10172A]">
                      <table className="min-w-[960px] border-collapse text-left text-xs">
                        <thead className="bg-[#0A0F1D] text-[10px] uppercase tracking-wide text-blue-200">
                          <tr>
                            <th className="px-3 py-3 font-semibold">Empresa</th>
                            <th className="px-3 py-3 font-semibold">Score</th>
                            <th className="px-3 py-3 font-semibold">Contacto</th>
                            <th className="px-3 py-3 font-semibold">Diagnóstico</th>
                            <th className="px-3 py-3 font-semibold">Primer contacto</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10 text-slate-200">
                          {leads.map((lead) => (
                            <tr key={`${lead.website}-${lead.name}`} className="align-top">
                              <td className="max-w-[180px] px-3 py-3">
                                <div className="font-medium text-white">{lead.name}</div>
                                {lead.website && (
                                  <a href={lead.website} target="_blank" rel="noreferrer" className="mt-1 block truncate text-blue-300 hover:underline">
                                    {lead.website}
                                  </a>
                                )}
                              </td>
                              <td className="px-3 py-3 font-semibold text-blue-300">{lead.score}/100</td>
                              <td className="max-w-[170px] px-3 py-3">
                                {lead.email && <a className="block break-all text-blue-300 hover:underline" href={`mailto:${lead.email}`}>{lead.email}</a>}
                                {lead.phone && <a className="mt-1 block text-slate-300 hover:underline" href={`tel:${lead.phone}`}>{lead.phone}</a>}
                                {lead.linkedin && <a className="mt-1 block text-blue-300 hover:underline" href={lead.linkedin} target="_blank" rel="noreferrer">LinkedIn</a>}
                                {lead.instagram && <a className="mt-1 block text-blue-300 hover:underline" href={lead.instagram} target="_blank" rel="noreferrer">Instagram</a>}
                                {!lead.email && !lead.phone && !lead.linkedin && !lead.instagram && <span>Formulario web</span>}
                              </td>
                              <td className="max-w-[240px] px-3 py-3 leading-5 text-slate-300">{lead.diagnosis}</td>
                              <td className="max-w-[340px] whitespace-pre-line px-3 py-3 leading-5 text-slate-300">{lead.outreach}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

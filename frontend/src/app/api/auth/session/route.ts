import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { authCookieName, backendApiUrl } from "@/lib/auth";

export const dynamic = "force-dynamic";

export async function GET() {
  const token = cookies().get(authCookieName)?.value;
  if (!token) {
    return NextResponse.json({ detail: "No hay una sesión activa." }, { status: 401 });
  }

  try {
    const upstream = await fetch(backendApiUrl("/api/auth/me"), {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const data = await upstream.json();
    const response = NextResponse.json(data, { status: upstream.status });
    if (upstream.status === 401) {
      response.cookies.delete(authCookieName);
    }
    return response;
  } catch {
    return NextResponse.json(
      { detail: "No se pudo verificar la sesión con el servidor." },
      { status: 502 },
    );
  }
}

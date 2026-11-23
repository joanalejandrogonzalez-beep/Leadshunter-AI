import { NextRequest, NextResponse } from "next/server";

import { authCookieName, authCookieOptions, backendApiUrl } from "@/lib/auth";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const upstream = await fetch(backendApiUrl("/api/auth/register"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    const response = NextResponse.json({
      user: data.user,
      organizations: data.organizations,
    }, { status: upstream.status });
    response.cookies.set(authCookieName, data.access_token, authCookieOptions(Boolean(body.remember_me)));
    return response;
  } catch {
    return NextResponse.json(
      { detail: "No se pudo conectar con el servicio de autenticación." },
      { status: 502 },
    );
  }
}

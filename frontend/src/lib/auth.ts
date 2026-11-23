export const authCookieName = "leadhunter_access_token";

export function backendApiUrl(path: string): string {
  const baseUrl = process.env.LEADHUNTER_API_URL || "http://127.0.0.1:8000";
  return `${baseUrl.replace(/\/+$/, "")}${path}`;
}

export function authCookieOptions(rememberMe: boolean) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    ...(rememberMe ? { maxAge: 30 * 24 * 60 * 60 } : {}),
  };
}

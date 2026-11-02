
const API_URL = process.env.API_URL ?? "http://localhost:7071";
const API_KEY = process.env.API_KEY ?? "";

export async function backend(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (API_KEY) headers.set("x-functions-key", API_KEY);
  return fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
}

// Pass a backend response straight through to the browser.
export async function relay(res: Response): Promise<Response> {
  return new Response(await res.text(), {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}

export function unreachable(err: unknown): Response {
  return Response.json(
    { ok: false, error: `Backend unreachable at ${API_URL}: ${String(err)}` },
    { status: 502 },
  );
}

export const backendUrl = API_URL;

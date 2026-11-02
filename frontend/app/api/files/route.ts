import { backend, relay, unreachable } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return await relay(await backend("/api/files"));
  } catch (err) {
    return unreachable(err);
  }
}

// Accepts multipart form data with a "file" field and forwards the bytes to Functions.
export async function POST(req: Request) {
  const form = await req.formData();
  const file = form.get("file");
  if (!(file instanceof File)) {
    return Response.json({ error: "Send a 'file' field" }, { status: 400 });
  }
  try {
    const res = await backend(`/api/files?name=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { "content-type": file.type || "application/octet-stream" },
      body: await file.arrayBuffer(),
    });
    return await relay(res);
  } catch (err) {
    return unreachable(err);
  }
}

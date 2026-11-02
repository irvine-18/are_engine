import { backend, relay, unreachable } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return await relay(await backend("/api/items"));
  } catch (err) {
    return unreachable(err);
  }
}

export async function POST(req: Request) {
  try {
    const res = await backend("/api/items", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: await req.text(),
    });
    return await relay(res);
  } catch (err) {
    return unreachable(err);
  }
}

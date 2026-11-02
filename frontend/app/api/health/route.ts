import { backend, relay, unreachable } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return await relay(await backend("/api/health"));
  } catch (err) {
    return unreachable(err);
  }
}

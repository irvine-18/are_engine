import { backend, backendUrl } from "@/lib/backend";
import Playground from "./playground";

export const dynamic = "force-dynamic";

type Check = { ok: boolean; error?: string; [k: string]: unknown };
type Health = { ok: boolean; checks?: Record<string, Check>; error?: string };

async function getHealth(): Promise<Health> {
  try {
    const res = await backend("/api/health");
    if (res.status === 401) return { ok: false, error: "401 from Functions: API_KEY missing or wrong" };
    return (await res.json()) as Health;
  } catch (err) {
    return { ok: false, error: `Cannot reach ${backendUrl}: ${String(err)}` };
  }
}

function Row({ label, check }: { label: string; check?: Check }) {
  const ok = check?.ok ?? false;
  const { ok: _ok, error, ...detail } = check ?? { ok: false };
  return (
    <li className={ok ? "ok" : "bad"}>
      <span className="dot">{ok ? "✓" : "✗"}</span>
      <strong>{label}</strong>
      <code>{error ?? (Object.keys(detail).length ? JSON.stringify(detail) : "not checked")}</code>
    </li>
  );
}

export default async function Home() {
  const health = await getHealth();
  const checks = health.checks ?? {};
  const host = process.env.CONTAINER_APP_NAME
    ? `${process.env.CONTAINER_APP_NAME} (${process.env.CONTAINER_APP_REVISION ?? "?"})`
    : "local dev server";

  return (
    <main>
      <h1>Connection check</h1>
      <ul className="checks">
        <Row label="Next.js frontend" check={{ ok: true, runningOn: host }} />
        <Row
          label="Azure Functions"
          check={checks.functions ?? { ok: false, error: health.error ?? "no response" }}
        />
        <Row label="Cosmos DB" check={checks.cosmos} />
        <Row label="Blob Storage" check={checks.storage} />
      </ul>
      <p className="muted">Backend: {backendUrl} · reload the page to re-check</p>
      <Playground />
    </main>
  );
}

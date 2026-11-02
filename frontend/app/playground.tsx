"use client";

import { useEffect, useState, type FormEvent } from "react";

type Item = { id: string; text: string; createdAt: string };
type Blob = { name: string; size: number; lastModified: string };

export default function Playground() {
  const [items, setItems] = useState<Item[]>([]);
  const [files, setFiles] = useState<Blob[]>([]);
  const [text, setText] = useState("");
  const [msg, setMsg] = useState("");

  async function load() {
    const [i, f] = await Promise.all([fetch("/api/items"), fetch("/api/files")]);
    if (i.ok) setItems(await i.json());
    if (f.ok) setFiles(await f.json());
  }

  useEffect(() => {
    load();
  }, []);

  async function addItem(e: FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/items", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
    });
    setMsg(res.ok ? "Item saved to Cosmos DB" : `Item failed: ${await res.text()}`);
    setText("");
    load();
  }

  async function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const res = await fetch("/api/files", { method: "POST", body: new FormData(form) });
    setMsg(res.ok ? "File uploaded to Blob Storage" : `Upload failed: ${await res.text()}`);
    form.reset();
    load();
  }

  return (
    <section className="grid">
      <div>
        <h2>Cosmos DB items</h2>
        <form onSubmit={addItem}>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Some text" required />
          <button>Save</button>
        </form>
        <ul>
          {items.map((it) => (
            <li key={it.id}>
              {it.text} <span className="muted">{new Date(it.createdAt).toLocaleString()}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>Blob Storage files</h2>
        <form onSubmit={upload}>
          <input type="file" name="file" required />
          <button>Upload</button>
        </form>
        <ul>
          {files.map((f) => (
            <li key={f.name}>
              {f.name} <span className="muted">{f.size} bytes</span>
            </li>
          ))}
        </ul>
      </div>
      {msg && <p className="msg">{msg}</p>}
    </section>
  );
}

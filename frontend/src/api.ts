const BASE = "http://localhost:8000";

export async function ingest(file?: File, transcript?: string) {
  const fd = new FormData();
  if (file) fd.append("file", file);
  if (transcript) fd.append("transcript", transcript);
  const r = await fetch(`${BASE}/ingest`, { method: "POST", body: fd });
  return r.json();
}

export async function generate(ingest_id: string) {
  const r = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingest_id }),
  });
  return r.json();
}

export async function save(patient_id: string, note: any) {
  const r = await fetch(`${BASE}/pms/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ patient_id, note }),
  });
  return r.json();
}

export async function audit() {
  const r = await fetch(`${BASE}/audit`);
  return r.json();
}

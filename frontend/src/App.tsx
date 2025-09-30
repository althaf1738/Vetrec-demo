import { useEffect, useMemo, useState, useRef } from "react";
import { ingest, generate, save, audit } from "./api";
import type { SOAPNote } from "./types";
import DiffPanel from "./components/DiffPanel";

type Tab = "editor" | "diff" | "audit";
type CompareMode = "generated" | "transcript";



function transcriptToNoteObj(txt: string): SOAPNote {
  // naive mapping: put full transcript into Subjective so changes show in Diff
  return {
    subjective: txt || "",
    objective: "",
    assessment: "",
    plan: ""
  };
}

export default function App(){
  const [file, setFile] = useState<File|null>(null);
  const [ingestId, setIngestId] = useState("");
  const [transcript, setTranscript] = useState("");
  const [note, setNote] = useState<SOAPNote | null>(null);
  const [originalNote, setOriginalNote] = useState<SOAPNote | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("editor");

  const [loadingIngest, setLoadingIngest] = useState(false);
  const [loadingGen, setLoadingGen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState("");
  const [compareMode, setCompareMode] = useState<CompareMode>("generated");
  const fileInputRef = useRef<HTMLInputElement>(null);



  const statusBadge = useMemo(()=>{
    if (saving || loadingGen || loadingIngest) return <span className="badge warn">Working…</span>;
    if (note) return <span className="badge ok">Ready</span>;
    return <span className="badge">Idle</span>;
  }, [saving, loadingGen, loadingIngest, note]);

  useEffect(()=>{
    if (!toast) return;
    const t = setTimeout(()=>setToast(""), 1200);
    return ()=>clearTimeout(t);
  }, [toast]);

  async function doIngest(){
    if (!file && !transcript.trim()) return;
    setLoadingIngest(true);
    try {
      const res = await ingest(file ?? undefined, transcript || undefined);
      setIngestId(res.ingest_id);
      setNote(null); setOriginalNote(null);
    } finally {
      setLoadingIngest(false);
    }
  }

  async function doGenerate(){
    if (!ingestId || loadingGen) return;
    setLoadingGen(true);
    try {
      const res = await generate(ingestId);
      setOriginalNote(res.note);
      setNote(res.note);
      setTab("editor");
  
      // 👇 clear the transcript after a successful generate
      setTranscript("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      setFile(null);
    } finally {
      setLoadingGen(false);
    }
  }
  

  async function doSave(){
    if (!note) return;
    setSaving(true);
    try {
      await save("patient-001", note);
      const a = await audit();
      setEvents(a.events);
      setToast("Saved ✓");
      setTab("audit");
    } finally {
      setSaving(false);
    }
  }

  const fields = (["subjective","objective","assessment","plan"] as const);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div style={{fontWeight:700}}>VetRec Demo</div>
        <div className="badge">LLM → SOAP → Review → Save</div>
        <div style={{marginLeft:"auto"}}>{statusBadge}</div>
      </header>

      <main className="main">
        {/* Left: ingest & generate */}
        <section className="card">
          <div className="head">
            <div>Ingest & Generate</div>
          </div>
          <div className="body">
            <div className="kv">
              <label>Audio file</label>
              <input  ref={fileInputRef} className="input" type="file" accept="audio/*"
                onChange={(e)=>setFile(e.target.files?.[0] ?? null)} />
              <div />
              <div className="help">Optional — you can also paste transcript below.</div>
            </div>

            <div className="kv">
              <label>Transcript</label>
              <textarea
                placeholder="Paste transcript here..."
                value={transcript}
                onChange={(e)=>setTranscript(e.target.value)}
              />
              <div />
              <div className="help">Short text keeps generation fast and consistent.</div>
            </div>

            <div className="row" style={{marginTop:10}}>
              <button className="button" onClick={doIngest} disabled={loadingIngest || (!file && !transcript.trim())}>
                {loadingIngest ? "Ingesting…" : "Ingest"}
              </button>
              <button className="button primary" onClick={doGenerate} disabled={!ingestId || loadingGen}>
                {loadingGen ? "Generating…" : "Generate SOAP"}
              </button>
            </div>

            {ingestId && (
              <div className="help" style={{marginTop:10}}>
                ingest_id: <code className="mono">{ingestId}</code>
              </div>
            )}
          </div>
        </section>

        {/* Right: editor/diff/audit */}
        <section className="card" style={{minHeight:420}}>
          <div className="head">
            <div>Review & Save</div>
          </div>

          <div className="tabbar">
            <button className={`tab ${tab==="editor"?"active":""}`} onClick={()=>setTab("editor")}>Editor</button>
            <button className={`tab ${tab==="diff"?"active":""}`} onClick={()=>setTab("diff")} disabled={!originalNote || !note}>Diff</button>
            <button className={`tab ${tab==="audit"?"active":""}`} onClick={()=>setTab("audit")}>Audit</button>
            {tab==="diff" && (
              <div style={{marginLeft:"auto", display:"flex", gap:8, alignItems:"center", paddingRight:8}}>
                <span className="help">Compare:</span>
                <select className="input" style={{width:190}} value={compareMode} onChange={e=>setCompareMode(e.target.value as CompareMode)}>
                  <option value="generated">Generated vs Current</option>
                  <option value="transcript">Transcript vs Current</option>
                </select>
              </div>
            )}
          </div>

          <div className="body">
            {tab==="editor" && (
              <>
                {!note && <div className="help">Generate to populate the SOAP fields.</div>}
                {note && (
                  <div style={{display:"grid", gap:10}}>
                    {fields.map((k)=>(
                      <div key={k}>
                        <div className="help" style={{marginBottom:6}}>{k.toUpperCase()}</div>
                        <textarea
                          value={(note as any)[k]}
                          onChange={(e)=>setNote({...note, [k]: e.target.value})}
                        />
                      </div>
                    ))}
                    <div className="row" style={{marginTop:4}}>
                      <button className="button success" onClick={doSave} disabled={saving}>
                        {saving ? "Saving…" : "Save to Mock PMS"}
                      </button>
                      {toast && <span className="help">{toast}</span>}
                    </div>
                  </div>
                )}
              </>
            )}

            {tab==="diff" && originalNote && note && (
              <DiffPanel
                before={compareMode === "generated" ? originalNote : transcriptToNoteObj(transcript)}
                after={note}
              />
            )}


            {tab==="audit" && (
              <div>
                <div className="help" style={{marginBottom:8}}>
                  Most recent events first
                </div>
                {events.length === 0 ? (
                  <div className="help">No events yet. Save a note to populate the audit log.</div>
                ) : (
                  <div className="mono small">
                    {events.map((ev,i)=>(
                      <div key={i} style={{padding:"6px 0", borderBottom:"1px solid var(--border)"}}>
                        <div><strong>{ev.action}</strong> <span className="help">• {ev.at_iso}</span></div>
                        <div className="help">{JSON.stringify(ev.meta)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

import json, datetime, aiosqlite
DB_PATH = "demo.sqlite3"

INIT_SQL = """
CREATE TABLE IF NOT EXISTS notes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL,
  content_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ingest(
  id TEXT PRIMARY KEY,
  file_path TEXT,
  transcript TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  meta_json TEXT NOT NULL,
  at_iso TEXT NOT NULL
);
"""

async def init():
  async with aiosqlite.connect(DB_PATH) as db:
    for stmt in INIT_SQL.strip().split(";"):
      if stmt.strip():
        await db.execute(stmt)
    await db.commit()

async def audit(action:str, meta:dict):
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute("INSERT INTO audit(action, meta_json, at_iso) VALUES(?,?,?)",
      (action, json.dumps(meta), datetime.datetime.utcnow().isoformat()))
    await db.commit()

async def create_ingest(ingest_id:str, file_path:str|None, transcript:str|None):
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(
      "INSERT OR REPLACE INTO ingest(id,file_path,transcript,created_at) VALUES(?,?,?,?)",
      (ingest_id, file_path, transcript, datetime.datetime.utcnow().isoformat()))
    await db.commit()

async def get_ingest(ingest_id:str):
  async with aiosqlite.connect(DB_PATH) as db:
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT * FROM ingest WHERE id=?", (ingest_id,))
    return await cur.fetchone()

async def save_note(patient_id:str, content:dict):
  async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(
      "INSERT INTO notes(patient_id, content_json, created_at) VALUES(?,?,?)",
      (patient_id, json.dumps(content), datetime.datetime.utcnow().isoformat()))
    await db.commit()

async def fetch_audit():
  async with aiosqlite.connect(DB_PATH) as db:
    db.row_factory = aiosqlite.Row
    cur = await db.execute("SELECT action, meta_json, at_iso FROM audit ORDER BY id DESC LIMIT 200")
    rows = await cur.fetchall()
    return [{"action": r["action"], "meta": json.loads(r["meta_json"]), "at_iso": r["at_iso"]} for r in rows]

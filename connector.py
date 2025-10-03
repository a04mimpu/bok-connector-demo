cat > connector.py <<'PY'
#!/usr/bin/env python3
import json, re, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
IN  = BASE / "bok_input.json"
OUT = BASE / "treserva.jsonl"   # JSON Lines
ACK = BASE / "acks.jsonl"
LOG = BASE / "run.log"

def sanitize_username(name: str) -> str:
    u = name.strip().lower()
    u = u.replace("å","a").replace("ä","a").replace("ö","o")
    u = re.sub(r"\s+", ".", u)
    u = re.sub(r"[^a-z0-9\.\-]", "", u)
    return u + "@goteborg.se"

def rules(p: dict) -> list:
    r = []
    if p.get("roll") == "Sjuksköterska" and p.get("enhet") == "Hisingen":
        r += ["Treserva-Bas","Treserva-Journalföring"]
    if p.get("roll") == "Undersköterska":
        r += ["Treserva-Bas"]
    if p.get("anstallningsform") == "konsult":
        r += ["Treserva-Tidsbegränsad"]
    return sorted(set(r))

def main():
    if not IN.exists():
        print(f"[Error] Saknar {IN}"); sys.exit(1)
    people = json.loads(IN.read_text(encoding="utf-8"))
    now = datetime.now().isoformat(timespec="seconds")

    out_lines, acks, logs = [], [], [f"[{now}] Start"]
    for i, p in enumerate(people, start=1):
        corr = f"corr-{i:03d}"
        try:
            if not p.get("namn"): raise ValueError("saknar 'namn'")
            if not p.get("personnummer"): raise ValueError("saknar 'personnummer'")
            username = sanitize_username(p["namn"])
            r = rules(p)
            if not r:
                acks.append({"correlationId":corr,"status":"FAIL","reason":"inga roller matchade reglerna","person":p})
                logs.append(f"[{corr}] FAIL: inga roller för {p.get('namn')}")
                continue
           out_lines.append({
    "op": "create",                     # eller p.get("op", "create") om du vill styra via input
    "externalId": p["personnummer"],
    "username": username,
    "displayName": p["namn"],
    "email": username,
    "roles": r,
    "jobTitle": p.get("roll"),          # <-- NYTT: Sjuksköterska
    "area": p.get("enhet"),             # <-- NYTT: Hisingen
    "source": "BoK",
    "timestamp": now
})
                
            })
            acks.append({"correlationId":corr,"status":"OK","roles":r,
                         "person":{"namn":p["namn"],"personnummer":p["personnummer"]}})
            logs.append(f"[{corr}] OK: {p['namn']} -> {r}")
        except Exception as e:
            acks.append({"correlationId":corr,"status":"FAIL","reason":str(e),"person":p})
            logs.append(f"[{corr}] ERROR: {e}")

    OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    ACK.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in acks) + ("\n" if acks else ""), encoding="utf-8")
    LOG.write_text("\n".join(logs) + "\n", encoding="utf-8")
    print(f"[Done] Skrev {len(out_lines)} rader till {OUT.name}, {len(acks)} kvittenser.")

if __name__ == "__main__":
    main()
PY

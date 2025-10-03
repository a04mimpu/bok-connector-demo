#!/usr/bin/env python3
import os, sys, json, re, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent
IN = BASE / "bok_input.json"
OUT = BASE / "treserva.jsonl"
ACK = BASE / "acks.jsonl"
LOG = BASE / "run.log"

def sanitize_username(name: str) -> str:
    u = name.strip().lower()
    # enkel transliteration
    u = u.replace("å","a").replace("ä","a").replace("ö","o")
    u = re.sub(r"\s+", ".", u)
    u = re.sub(r"[^a-z0-9\.\-]", "", u)
    return u + "@goteborg.se"

def rules(p: dict) -> list:
    roles = []
    if p.get("roll") == "Sjuksköterska" and p.get("enhet") == "Hisingen":
        roles += ["Treserva-Bas", "Treserva-Journalföring"]
    if p.get("roll") == "Undersköterska":
        roles += ["Treserva-Bas"]
    if p.get("anstallningsform") == "konsult":
        roles += ["Treserva-Tidsbegränsad"]
    return sorted(set(roles))

def main():
    now = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[Info] BASE={BASE}")
    print(f"[Info] Reading {IN}")
    if not IN.exists():
        print(f"[Error] {IN} saknas"); sys.exit(1)

    try:
        people = json.loads(IN.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Error] Kunde inte läsa {IN}: {e}")
        sys.exit(1)

    acks, out, log_lines = [], [], [f"[{now}] Start connector run"]

    for i, p in enumerate(people, start=1):
        corr = f"corr-{i:03d}"
        try:
            if not p.get("namn"): raise ValueError("saknar 'namn'")
            if not p.get("personnummer"): raise ValueError("saknar 'personnummer'")
            username = sanitize_username(p["namn"])
            r = rules(p)
            if not r:
                acks.append({"correlationId": corr, "status": "FAIL",
                             "reason": "inga roller matchade reglerna", "person": p})
                log_lines.append(f"[{corr}] FAIL: inga roller för {p.get('namn')} ({p.get('roll')}, {p.get('enhet')})")
                continue
            tres = {
                "op": "create",
                "externalId": p["personnummer"],
                "username": username,
                "displayName": p["namn"],
                "email": username,
                "roles": r,
                "source": "BoK",
                "timestamp": now
            }
            out.append(tres)
            acks.append({"correlationId": corr, "status": "OK",
                         "roles": r, "person": {"namn": p["namn"], "personnummer": p["personnummer"]}})
            log_lines.append(f"[{corr}] OK: {p['namn']} -> {r}")
        except Exception as e:
            acks.append({"correlationId": corr, "status": "FAIL", "reason": str(e), "person": p})
            log_lines.append(f"[{corr}] ERROR: {e}")

    print(f"[Info] Writing {OUT}")
    with OUT.open("w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[Info] Writing {ACK}")
    with ACK.open("w", encoding="utf-8") as f:
        for a in acks:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    print(f"[Info] Writing {LOG}")
    LOG.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print(f"[Done] Wrote {len(out)} treserva rows, {len(acks)} acks")

if __name__ == "__main__":
    main()

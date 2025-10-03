# BoK Connector Demo

Detta är en liten demo som visar hur BoK kan prata med ett verksamhetssystem (ex. Treserva) via en **connector**.

## 📂 Innehåll
- `connector.py` – kod som översätter från HR/BoK till en Treserva-importfil.
- `bok_input.json` – exempeldata (nyanställningar, roller, enheter).

När du kör connectorn skapas:
- `treserva.jsonl` – det som systemet (Treserva) skulle kunna importera.
- `acks.jsonl` – kvittenser (OK/FAIL) för varje rad i input.
- `run.log` – en enkel logg.

## 🚀 Så här kör du

### 1. Öppna i GitHub Codespaces
- Klicka på **Code → Create codespace on main**.

### 2. Kör connectorn
I terminalen:
```bash
python connector.py

# 🛡️ Auther Guard AI

**Space & Terrestrial Weather Station** — Flask web edition

Rebuilt from the original Tkinter desktop app to fix platform issues (e.g. invalid `#ffffffaa` color on some Tcl/Tk builds) and deliver a modern, attractive browser UI.

## Features

- **Live dashboard** — solar wind, IMF Bz, flares, CME probability, Kp, Dst, TEC, aurora, terrestrial meteo
- **Risk assessment** — power grids, GPS, aviation, satellites, HF radio, aurora
- **Graphical analyzer** — Chart.js time series + statistics
- **Prediction Lab** — shared learner / technical modes (no expert gate)
- **Teach** — space-weather lessons + CME animation + AI Q&A
- **Multi-AI chat** — Claude, Gemini, DeepSeek, GPT, Grok + **Local** knowledge fallback
- **AES-256-CTR `.AG` archives** — encrypted export/import of observation history
- **Deep Learning lab** — educational Random Forest (Kp≥5 storm flag)
- **Strong password login** (same policy as original: length + complexity)

## Quick start

```bash
cd auther_guard_ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open **http://127.0.0.1:5000** → create account on first login (strong password required).

### Docker

```bash
docker compose up --build
```

## API (authenticated session)

| Endpoint | Description |
|----------|-------------|
| `GET /api/latest` | Latest observation + risk |
| `POST /api/live` | New simulated sample |
| `GET /api/history` | Recent records |
| `GET /api/series/<key>` | Time series |
| `POST /api/predict` | Prediction Lab |
| `POST /api/chat` | Multi-AI Q&A |
| `POST /api/export/ag` | Download encrypted archive |
| `POST /api/import/ag` | Upload `.AG` |
| `POST /api/ml/train` | Train educational classifier |

## Configuration

Optional API keys in `.env` or **Settings** (session):

- `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`

Without keys, the app uses a local space-weather knowledge base.

## Notes

- Live values are **educational simulations** (plus sample NOAA-style storm sequence on first load). Wire NOAA SWPC JSON feeds for production monitoring.
- Encryption uses PBKDF2-HMAC-SHA256 (100k iterations) + AES-256-CTR — same design intent as the desktop `.AG` format.
- ML model is **not** an operational forecast product.

## Project layout

```
auther_guard_ai/
├── app/
│   ├── routes/     # main, auth, api
│   ├── services/   # weather_engine, ai_client, crypto_store
│   ├── templates/  # dashboard, analyzer, prediction, teach, chat…
│   └── static/
├── data/
├── run.py
├── Dockerfile
└── README.md
```

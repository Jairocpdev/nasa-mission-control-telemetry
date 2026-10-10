# 🛰️ NASA Mission Control Telemetry - SAT-01

[ONLINE](https://img.shields.io/badge/STATUS-ONLINE_16170+-brightgreen?style=for-the-badge) 
[Autonomous](https://img.shields.io/badge/MODE-AUTONOMOUS-no--terminal--needed-blue?style=for-the-badge)
[Stack](https://img.shields.io/badge/Stack-Angular_FastAPI_Supabase-0f172a?style=for-the-badge)

> **FOOOOI!** Depois de `toFixed crash`, `Redis 1225`, `Docker fail`, `CORS 401` e números fixos em `99.84%` por 1 dia - agora é **100% autônomo, sem depender de terminal**.

**Live Demo:** https://nasa-mission-control-telemetry-rho.vercel.app/  
**API:** https://nasa-mission-control-api-vpn1.onrender.com  
**Health:** https://nasa-mission-control-api-vpn1.onrender.com/health → `{"telemetry_count":16170+,"satellite_autonomous":true}`

---

## 🚀 O que foi corrigido (jornada)

1. **v1 - Quebrado:** `Cannot read properties of undefined (reading 'toFixed')` no `app.component.ts:16` - frontend Angular crashava antes da API responder
2. **v2 - Local dependente:** `direct-inject-live.py` → Supabase funcionou (`16134 packets`) mas dependia de terminal aberto, fechou = números fixos
3. **v3 - AUTÔNOMO (atual):** Satélite roda DENTRO da API no Render via `lifespan` + `satellite_loop()` - `+1 pacote/s` mesmo com PC desligado

## 🏗️ Arquitetura Final - No Terminal Needed

```
[Render FastAPI v3.0-AUTONOMOUS] --lifespan--> satellite_loop() --1/s--> [Supabase TimescaleDB]
        |                                                               |
        |-- /telemetry/latest, /history, /ws/telemetry, /health        |
        v                                                               |
[Vercel Angular] --fetch 2s--> REST + WS LIVE --display--> NASA Dashboard
        BATTERY 87.90% | TEMPERATURE -13.45°C | ALTITUDE 419.62km | SIGNAL 93.89%
```

**Antes:** `satellite.py → Redis (localhost:6379) → ingestor.py → Postgres` (precisava Docker, Redis)  
**Agora:** `API lifespan → Supabase direto (asyncpg)` - sem Docker, sem Redis, sem terminal

## 🔧 Stack

- **Frontend:** Angular 17 standalone `imports: [CommonModule, HttpClientModule]` + `safe(n)` guard pra `toFixed`
  - Build: `ng build` → `221.35 kB main | 59.98 kB transfer` - `Application bundle generation complete`
- **Backend:** FastAPI v3.0 + SQLAlchemy async + asyncpg + lifespan background task
  - `allow_credentials=False` fix CORS `site.webmanifest 401` + `allow_origins=["*"]`
  - `statement_cache_size=0` fix pgbouncer Supabase + SSL `CERT_NONE`
- **DB:** Supabase Postgres + TimescaleDB - tabela `telemetry (timestamp, sat_id, battery, temperature, altitude, signal)`
- **Deploy:** Render (API + satélite autônomo) + Vercel (Angular)

## 📦 Endpoints

- `GET /` → `{"status":"NASA ONLINE AUTONOMOUS","mode":"self-generating"}`
- `GET /health` → `{"status":"OK","telemetry_count":16170,"satellite_autonomous":true,"mode":"no-terminal-needed"}`
- `GET /telemetry/latest` → último pacote
- `GET /telemetry/history?limit=100&order=desc` → últimos 100
- `WS /ws/telemetry` → push a cada 0.5s

## 🖥️ Como rodar local (opcional - não precisa mais)

```bash
# Backend já é autônomo no Render, mas se quiser local:
cd backend
pip install -r requirements.txt # fastapi sqlalchemy asyncpg python-dotenv
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
ng serve # http://localhost:4200
npm run build # dist/frontend
```

## 🗑️ Cleanup - O que foi apagado

- `backend/simulator/` inteiro incluindo `direct-inject-live.py` - era o que prendia ao terminal
- `backend/app/ingestor.py` - antigo consumidor Redis
- `docker run -p 6379:6379 redis` - não precisa mais

## ✅ Validação final

```powershell
curl.exe https://nasa-mission-control-api-vpn1.onrender.com/health
# {"status":"OK","telemetry_count":16158,"satellite_autonomous":true,"mode":"no-terminal-needed"}
# 10s depois:
# {"status":"OK","telemetry_count":16167,"satellite_autonomous":true,"mode":"no-terminal-needed"}
# +9 em 10s = 1/s vivo!
```

**Frontend:** https://nasa-mission-control-telemetry-rho.vercel.app/ mostra `ONLINE - 16170 packets` com BAT/TEMP/ALT/SIG mudando sozinho.

---

**Commit:** `feat: satellite autonomous v3 - no-terminal-needed + README final`  
**Autor:** Jairo Andrade - Nilópolis, RJ  
**Status:** 🛰️ ONLINE AUTONOMOUS
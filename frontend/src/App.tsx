import React, { useEffect, useState, useRef, useMemo } from "react";

const API_BASE = "https://nasa-mission-control-api-vpn1.onrender.com";
const WS_URL = "wss://nasa-mission-control-api-vpn1.onrender.com/ws/telemetry";

type Telemetry = {
  timestamp: string;
  sat_id: string;
  battery: number;
  temperature: number;
  altitude: number;
  signal: number;
};

type Health = { status: string; telemetry_count: number; };

const safe = (v: any, d=0) => typeof v === 'number' && !isNaN(v) ? v : d;

export default function App() {
  const [latest, setLatest] = useState<Telemetry | null>(null);
  const [history, setHistory] = useState<Telemetry[]>([]);
  const [status, setStatus] = useState<"CONNECTING" | "ONLINE" | "OFFLINE">("CONNECTING");
  const [count, setCount] = useState(0);
  const [wsLive, setWsLive] = useState(false);
  const [now, setNow] = useState(new Date());
  const [flashKey, setFlashKey] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const latestRef = useRef<Telemetry | null>(null);

  useEffect(() => { latestRef.current = latest; }, [latest]);
  useEffect(() => { const id = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(id); }, []);

  useEffect(() => {
    let mounted = true;
    const fetchHealth = async () => {
      try {
        const r = await fetch(`${API_BASE}/health`);
        const j: Health = await r.json();
        if (!mounted) return;
        if (j.status === "OK") { setStatus("ONLINE"); setCount(j.telemetry_count); } else setStatus("ONLINE");
      } catch { if (mounted) setStatus("OFFLINE"); }
    };
    const fetchLatest = async () => {
      try {
        const r = await fetch(`${API_BASE}/telemetry/latest`);
        const j = await r.json();
        if (!mounted) return;
        if (j?.sat_id) { setLatest(j); setFlashKey(j.timestamp); setTimeout(()=>setFlashKey(""),400); }
      } catch {}
    };
    const fetchHistory = async () => {
      try {
        const r = await fetch(`${API_BASE}/telemetry/history?limit=100&order=desc`);
        const j = await r.json();
        if (!mounted) return;
        if (Array.isArray(j)) { setHistory(j.filter(Boolean)); if (!latestRef.current && j[0]?.sat_id) setLatest(j[0]); }
      } catch {}
    };
    fetchHealth(); fetchLatest(); fetchHistory();
    const idH = setInterval(fetchHealth, 3000);
    const idL = setInterval(fetchLatest, 2000);
    const idHi = setInterval(fetchHistory, 5000);
    return () => { mounted=false; clearInterval(idH); clearInterval(idL); clearInterval(idHi); };
  }, []);

  useEffect(() => {
    let timer: any;
    const connect = () => {
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;
        ws.onopen = () => setWsLive(true);
        ws.onclose = () => { setWsLive(false); timer=setTimeout(connect,2500); };
        ws.onerror = () => { setWsLive(false); ws.close(); };
        ws.onmessage = (e) => {
          try {
            const d = JSON.parse(e.data);
            if (d?.sat_id) {
              setLatest(d); setFlashKey(d.timestamp||String(Date.now()));
              setTimeout(()=>setFlashKey(""),400);
              setHistory(prev=>[d, ...prev].slice(0,100));
            }
          } catch {}
        };
      } catch { setWsLive(false); timer=setTimeout(connect,3000); }
    };
    connect();
    return () => { clearTimeout(timer); wsRef.current?.close(); };
  }, []);

  const chartData = useMemo(() => {
    return [...history].filter(h=>h && typeof h.timestamp==='string').reverse().slice(-50).map(h=>({
      t: new Date(h.timestamp).toLocaleTimeString([], {hour12:false, minute:"2-digit", second:"2-digit"}),
      battery: Number(safe(h.battery).toFixed(2)),
      temp: Number(safe(h.temperature).toFixed(2)),
      alt: Number(safe(h.altitude).toFixed(2)),
      sig: Number(safe(h.signal).toFixed(2)),
      ts: h.timestamp
    }));
  }, [history]);

  const batteryStatus = latest ? (safe(latest.battery)<20?"CRITICAL":safe(latest.battery)<40?"LOW":"NOMINAL") : "—";
  const tempStatus = latest ? (safe(latest.temperature)<-10 || safe(latest.temperature)>35?"WARNING":"NOMINAL") : "—";

  return (
    <div className="min-h-screen w-full bg-[#020617] text-slate-200 font-mono antialiased overflow-x-hidden">
      <style>{`
        *{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"JetBrains Mono",monospace}
        .glow-green{box-shadow:0 0 0 1px rgba(34,197,94,0.3),0 0 20px rgba(34,197,94,0.15)}
        .glow-border{box-shadow:0 0 0 1px #1e293b}
        .glow-border:hover{box-shadow:0 0 0 1px #334155,0 0 24px rgba(56,189,248,0.08)}
        .grid-bg{background-image:linear-gradient(rgba(148,163,184,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(148,163,184,0.04) 1px,transparent 1px);background-size:32px 32px}
        ::-webkit-scrollbar{width:6px;height:6px}::-webkit-scrollbar-thumb{background:#1e293b;border-radius:999px}
      `}</style>
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(56,189,248,0.12),_transparent_60%)]" />
        <div className="absolute inset-0 grid-bg opacity-60" />
      </div>
      <div className="relative z-10 max-w-[1440px] mx-auto px-4 md:px-6 py-6">
        <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border border-slate-800 bg-[#0f172a]/80 backdrop-blur-xl rounded-[14px] px-5 py-4">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 rounded-[9px] bg-white text-black grid place-items-center font-bold text-[11px]">NASA</div>
            <div>
              <h1 className="text-[18px] md:text-[20px] font-bold tracking-[0.18em]">NASA MISSION CONTROL // SAT-01</h1>
              <div className="flex items-center gap-3 mt-1.5 text-[11px] tracking-widest text-slate-400">
                <span className="inline-flex items-center gap-2">
                  <span className={`w-[8px] h-[8px] rounded-full ${status==="ONLINE"?"bg-emerald-400":"bg-amber-400"}`} />
                  <span className={status==="ONLINE"?"text-emerald-300":""}>{status}</span>
                </span>
                <span className="w-px h-3 bg-slate-700" />
                <span>{count.toLocaleString()} PACKETS</span>
                <span className="w-px h-3 bg-slate-700 hidden md:block" />
                <span className={`hidden md:inline-flex gap-1.5 ${wsLive?"text-cyan-300":"text-slate-500"}`}>● WS {wsLive?"LIVE":"OFF"}</span>
              </div>
            </div>
          </div>
          <div className="text-[11px] text-slate-400">{now.toISOString().replace('T',' ').slice(0,19)}Z</div>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          <div className="border bg-[#0f172a] rounded-[12px] p-5">
            <div className="text-[11px] tracking-[0.2em] text-slate-500">BATTERY — {batteryStatus}</div>
            <div className="mt-3 text-[36px] font-bold">{latest ? safe(latest.battery).toFixed(2) : "--"}<span className="text-[18px] opacity-60">%</span></div>
            <div className="mt-3 h-[2px] bg-slate-800"><div className="h-full bg-emerald-400" style={{width:`${latest?Math.min(100,safe(latest.battery)):0}%`}} /></div>
          </div>
          <div className="border border-slate-800 bg-[#0f172a] rounded-[12px] p-5">
            <div className="text-[11px] tracking-[0.2em] text-slate-500">TEMPERATURE — {tempStatus}</div>
            <div className="mt-3 text-[36px] font-bold">{latest ? safe(latest.temperature).toFixed(2) : "--"}<span className="text-[18px] opacity-60">°C</span></div>
          </div>
          <div className="border border-slate-800 bg-[#0f172a] rounded-[12px] p-5">
            <div className="text-[11px] tracking-[0.2em] text-slate-500">ALTITUDE</div>
            <div className="mt-3 text-[36px] font-bold">{latest ? safe(latest.altitude).toFixed(2) : "--"}<span className="text-[18px] opacity-60"> KM</span></div>
          </div>
          <div className="border border-slate-800 bg-[#0f172a] rounded-[12px] p-5">
            <div className="text-[11px] tracking-[0.2em] text-slate-500">SIGNAL</div>
            <div className="mt-3 text-[36px] font-bold">{latest ? safe(latest.signal).toFixed(2) : "--"}<span className="text-[18px] opacity-60">%</span></div>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4 mt-5">
          <div className="col-span-12 lg:col-span-8">
            <div className="border border-slate-800 bg-[#0f172a]/90 rounded-[12px] overflow-hidden">
              <div className="flex justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/40 text-[11px] tracking-widest">
                <span>LIVE TELEMETRY LOG — LAST 100</span><span>{wsLive?"WS LIVE":"POLL 2S"}</span>
              </div>
              <div className="overflow-auto max-h-[520px]">
                <div className="min-w-[680px]">
                  <div className="grid grid-cols-[140px_1fr_1fr_1fr_1fr_90px] gap-2 px-4 py-2 bg-[#0f172a] border-b border-slate-800 text-[10px] text-slate-500 tracking-widest">
                    <span>TIMESTAMP</span><span>BATTERY</span><span>TEMP</span><span>ALT</span><span>SIGNAL</span><span className="text-right">SAT</span>
                  </div>
                  {history.length===0?<div className="p-8 text-center text-slate-500 text-[12px]">Awaiting telemetry...</div>:
                  history.map((h,i)=>(
                    <div key={`${h.timestamp}-${i}`} className={`grid grid-cols-[140px_1fr_1fr_1fr_1fr_90px] gap-2 px-4 py-[7px] border-b border-slate-800/60 text-[12px] ${i===0&&flashKey?"bg-cyan-500/10":""}`}>
                      <span className="text-slate-400">{new Date(h.timestamp).toISOString().slice(11,19)}</span>
                      <span className="text-emerald-300">{safe(h.battery).toFixed(2)}%</span>
                      <span className="text-slate-200">{safe(h.temperature).toFixed(2)}°C</span>
                      <span className="text-violet-200">{safe(h.altitude).toFixed(1)} km</span>
                      <span className="text-cyan-200">{safe(h.signal).toFixed(1)}%</span>
                      <span className="text-right text-[10px] text-slate-500">{h.sat_id}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="col-span-12 lg:col-span-4 space-y-4">
            <div className="border border-slate-800 bg-[#0f172a] rounded-[12px] p-4">
              <div className="text-[11px] tracking-[0.2em] text-slate-500">CURRENT PACKET</div>
              <pre className="mt-3 bg-black/40 border border-slate-800 p-3 rounded text-[11px] overflow-auto">{JSON.stringify(latest, null, 2) || "waiting..."}</pre>
            </div>
            <div className="border border-slate-800 bg-[#0f172a]/80 rounded-[12px] p-4 text-[11px]">
              <div className="tracking-[0.2em] text-slate-500">SYSTEM LINK</div>
              <div className="mt-2 space-y-1"><div>REST: {API_BASE}</div><div>WS: {WS_URL}</div><div>DB: Supabase ✓</div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

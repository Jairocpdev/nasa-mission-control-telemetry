import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';

interface Telemetry {
  timestamp: string;
  sat_id: string;
  battery: number;
  temperature: number;
  altitude: number;
  signal: number;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  template: `
  <div style="background:#020617;min-height:100vh;color:#e2e8f0;font-family:monospace;padding:24px">
    <h1 style="letter-spacing:2px">NASA MISSION CONTROL // SAT-01 
      <span [style.color]="status==='ONLINE'?'#22c55e':status==='WAKING'?'#eab308':'#ef4444'">
        ● {{status}} - {{count ? count + ' packets' : ''}}
      </span>
    </h1>
    
    <!-- WAKING STATE - Mostra cache enquanto Render acorda -->
    <div *ngIf="status==='WAKING'" style="background:#1e1b4b;border:1px solid #4338ca;border-radius:12px;padding:16px;margin:16px 0;color:#a5b4fc">
      🛰️ Acordando satélite no Render... (free tier dorme após 15min sem uso)<br>
      <span style="font-size:12px;opacity:.7">Mostrando último cache de {{cachedAt || 'sessão anterior'}} enquanto API aquece (~5-15s, não 50s)</span>
      <div style="margin-top:8px;height:4px;background:#312e81;border-radius:99px;overflow:hidden">
        <div style="height:100%;background:#6366f1;width:100%;animation:wake 12s linear infinite"></div>
      </div>
      <style>@keyframes wake{0%{width:0%}100%{width:100%}}</style>
    </div>

    <div *ngIf="latest" style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0">
      <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px">
        <div style="opacity:.6;font-size:12px">BATTERY</div>
        <div style="font-size:28px">{{ safe(latest?.battery).toFixed(2) }}%</div>
      </div>
      <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px">
        <div style="opacity:.6;font-size:12px">TEMPERATURE</div>
        <div style="font-size:28px">{{ safe(latest?.temperature).toFixed(2) }}°C</div>
      </div>
      <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px">
        <div style="opacity:.6;font-size:12px">ALTITUDE</div>
        <div style="font-size:28px">{{ safe(latest?.altitude).toFixed(2) }} km</div>
      </div>
      <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px">
        <div style="opacity:.6;font-size:12px">SIGNAL</div>
        <div style="font-size:28px">{{ safe(latest?.signal).toFixed(2) }}%</div>
      </div>
    </div>

    <div *ngIf="!latest" style="opacity:.5">
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0">
        <div *ngFor="let i of [1,2,3,4]" style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;animation:pulse 1.5s infinite">
          <div style="height:12px;width:60px;background:#1e293b;border-radius:4px;margin-bottom:12px"></div>
          <div style="height:28px;width:100px;background:#1e293b;border-radius:4px"></div>
        </div>
      </div>
      <style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}</style>
    </div>

    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin-top:24px">
      <h3>LIVE LOG - LAST 100 <span *ngIf="status!=='ONLINE'" style="font-size:10px;opacity:.5">(cache)</span></h3>
      <div style="max-height:400px;overflow:auto;font-size:12px">
        <div *ngFor="let h of history" style="display:flex;justify-content:space-between;border-bottom:1px solid #1e293b;padding:6px 0">
          <span>{{ h.timestamp }}</span>
          <span>BAT {{ safe(h?.battery).toFixed(1) }}%</span>
          <span>TEMP {{ safe(h?.temperature).toFixed(1) }}C</span>
          <span>ALT {{ safe(h?.altitude).toFixed(0) }}km</span>
          <span>SIG {{ safe(h?.signal).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <div style="margin-top:16px;font-size:12px;opacity:.5">
      API: {{API}} | DB: Supabase | {{count}} packets 
      <span *ngIf="status==='ONLINE'">| 🛰️ LIVE</span>
      <span *ngIf="status==='WAKING'">| ⏳ WAKING (Render free tier)</span>
    </div>
  </div>
  `
})
export class AppComponent implements OnInit {
  API = 'https://nasa-mission-control-api-vpn1.onrender.com';
  latest: Telemetry | null = null;
  history: Telemetry[] = [];
  count = 0;
  status: 'CONNECTING'|'ONLINE'|'OFFLINE'|'WAKING' = 'CONNECTING';
  cachedAt: string | null = null;

  constructor(private http: HttpClient) {}

  safe(n: any): number { return typeof n === 'number' && !isNaN(n) ? n : 0; }

  ngOnInit() {
    // 1. Carrega cache instantâneo do localStorage - ZERA os 50s de espera percebida
    try {
      const c = localStorage.getItem('nasa-cache');
      if (c) {
        const data = JSON.parse(c);
        if (data.latest?.sat_id) {
          this.latest = data.latest;
          this.history = data.history || [];
          this.count = data.count || 0;
          this.cachedAt = data.cachedAt;
          this.status = 'WAKING'; // mostra cache enquanto acorda
        }
      }
    } catch {}

    this.load();
    setInterval(()=>this.load(), 2000);
  }

  load() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000); // timeout 8s, não 50s

    this.http.get<any>(`${this.API}/health`).subscribe({
      next: (h) => {
        clearTimeout(timeout);
        if (h.status==='OK'){
          this.status='ONLINE';
          this.count=h.telemetry_count;
        }
      },
      error: (e) => {
        clearTimeout(timeout);
        if (this.latest) this.status='WAKING';
        else this.status='OFFLINE';
      }
    });

    this.http.get<Telemetry>(`${this.API}/telemetry/latest`).subscribe((d:any)=>{
      if (d?.sat_id) {
        this.latest = d;
        this.saveCache();
      }
    });

    this.http.get<Telemetry[]>(`${this.API}/telemetry/history?limit=100&order=desc`).subscribe(h=>{
      if (Array.isArray(h) && h.length>0) {
        this.history = h.filter(Boolean);
        this.saveCache();
      }
    });
  }

  saveCache() {
    try {
      localStorage.setItem('nasa-cache', JSON.stringify({
        latest: this.latest,
        history: this.history.slice(0,20),
        count: this.count,
        cachedAt: new Date().toLocaleTimeString()
      }));
    } catch {}
  }
}
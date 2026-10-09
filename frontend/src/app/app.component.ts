
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
      <span [style.color]="status==='ONLINE'?'#22c55e':'#ef4444'">● {{status}} - {{count}} packets</span>
    </h1>
    
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

    <div *ngIf="!latest" style="opacity:.5">Loading telemetry from {{API}}... (Render free tier dorme 50s na primeira req)</div>

    <div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px;margin-top:24px">
      <h3>LIVE LOG - LAST 100</h3>
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

    <div style="margin-top:16px;font-size:12px;opacity:.5">API: {{API}} | DB: Supabase TimescaleDB - 16134 packets OK</div>
  </div>
  `
})
export class AppComponent implements OnInit {
  API = 'https://nasa-mission-control-api-vpn1.onrender.com';
  latest: Telemetry | null = null;
  history: Telemetry[] = [];
  count = 0;
  status: 'CONNECTING'|'ONLINE'|'OFFLINE' = 'CONNECTING';

  constructor(private http: HttpClient) {}

  safe(n: any): number { return typeof n === 'number' && !isNaN(n) ? n : 0; }

  ngOnInit() {
    this.load();
    setInterval(()=>this.load(), 2000);
  }

  load() {
    this.http.get<any>(`${this.API}/health`).subscribe({
      next: (h) => { if (h.status==='OK'){ this.status='ONLINE'; this.count=h.telemetry_count; } },
      error: () => this.status='OFFLINE'
    });
    this.http.get<Telemetry>(`${this.API}/telemetry/latest`).subscribe((d:any)=>{
      if (d?.sat_id) this.latest = d;
    });
    this.http.get<Telemetry[]>(`${this.API}/telemetry/history?limit=100&order=desc`).subscribe(h=>{
      if (Array.isArray(h)) this.history = h.filter(Boolean);
    });
  }
}

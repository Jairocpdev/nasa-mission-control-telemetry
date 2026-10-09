
import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

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
  template: `
  <div class="nasa-wrap">
    <style>
      .nasa-wrap{background:#020617;min-height:100vh;color:#e2e8f0;font-family:monospace;padding:24px}
      .card{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:16px}
      .grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}
      @media(max-width:800px){.grid4{grid-template-columns:1fr 1fr}}
      .online{color:#22c55e} .offline{color:#ef4444}
      .log{max-height:400px;overflow:auto;font-size:12px}
      .row{display:flex;justify-content:space-between;border-bottom:1px solid #1e293b;padding:6px 0}
    </style>
    <h1>NASA MISSION CONTROL // SAT-01 <span [class]="status==='ONLINE'?'online':'offline'">● {{status}} - {{count}} packets</span></h1>
    
    <div class="grid4" *ngIf="latest">
      <div class="card"><div>BATTERY</div><div style="font-size:28px">{{ safe(latest?.battery).toFixed(2) }}%</div></div>
      <div class="card"><div>TEMPERATURE</div><div style="font-size:28px">{{ safe(latest?.temperature).toFixed(2) }}°C</div></div>
      <div class="card"><div>ALTITUDE</div><div style="font-size:28px">{{ safe(latest?.altitude).toFixed(2) }} km</div></div>
      <div class="card"><div>SIGNAL</div><div style="font-size:28px">{{ safe(latest?.signal).toFixed(2) }}%</div></div>
    </div>
    <div *ngIf="!latest">Loading telemetry from {{API}}...</div>

    <div class="card">
      <h3>LIVE LOG - LAST 100</h3>
      <div class="log">
        <div class="row" *ngFor="let h of history">
          <span>{{ h.timestamp | date:'HH:mm:ss' }}</span>
          <span>BAT {{ safe(h?.battery).toFixed(1) }}%</span>
          <span>TEMP {{ safe(h?.temperature).toFixed(1) }}C</span>
          <span>ALT {{ safe(h?.altitude).toFixed(0) }}km</span>
          <span>SIG {{ safe(h?.signal).toFixed(0) }}%</span>
        </div>
      </div>
    </div>
  </div>
  `,
  styles: []
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
    this.http.get<Telemetry>(`${this.API}/telemetry/latest`).subscribe(d=>{
      if ((d as any)?.sat_id) this.latest = d as any;
    });
    this.http.get<Telemetry[]>(`${this.API}/telemetry/history?limit=100&order=desc`).subscribe(h=>{
      if (Array.isArray(h)) this.history = h.filter(Boolean);
    });
  }
}

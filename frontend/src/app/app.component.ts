import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div style="background:#000;color:#0f0;font-family:'Courier New',monospace;min-height:100vh;padding:30px">
    <h1>🛰 NASA MISSION CONTROL TELEMETRY</h1>
    <h3 style="color:#888">SAT-01 | TimescaleDB + Redis + FastAPI + Angular 19</h3>

    <div *ngIf="latest" style="border:1px solid #0f0;padding:20px;margin-top:20px;background:#0a0a0a">
      <h2>LIVE TELEMETRY ({{count}} packets ingested)</h2>
      <p>TIMESTAMP: {{latest.timestamp}}</p>
      <p>BATTERY: <span [style.color]="latest.battery < 20? 'red' : latest.battery < 50? 'orange' : '#0f0'">{{latest.battery.toFixed(2)}}% {{latest.battery < 20? 'CRITICAL' : latest.battery < 50? 'WARNING' : 'NOMINAL'}}</span></p>
      <p>TEMPERATURE: {{latest.temperature.toFixed(2)}}°C</p>
      <p>ALTITUDE: {{latest.altitude.toFixed(2)}} km</p>
      <p>SIGNAL: {{latest.signal.toFixed(2)}}%</p>
      <p>SAT_ID: {{latest.sat_id}}</p>
    </div>

    <div *ngIf="!latest" style="margin-top:30px">📡 Connecting to backend...</div>

    <div style="margin-top:30px;color:#555;font-size:12px">
      Pipeline: satellite.py (2msg/s) → Redis → ingestor.py → mission_control (hypertable) → FastAPI → Angular
    </div>
  </div>
  `,
})
export class AppComponent implements OnInit {
  latest: any = null;
  count = 0;
  // TROCA PRA SUA URL DA VERCEL/RENDER QUANDO FOR PRA PROD
  API = 'http://localhost:8000';

  async ngOnInit() {
    const load = async () => {
      try {
        // 1. Pega o ÚLTIMO pacote de verdade
        const rLatest = await fetch(`${this.API}/telemetry/latest`);
        if (rLatest.ok) {
          this.latest = await rLatest.json();
        } else {
          // fallback se não tiver /latest, pega o último do history DESC
          const rHist = await fetch(`${this.API}/telemetry/history?limit=1&order=desc`);
          const jHist = await rHist.json();
          if (jHist.length > 0) this.latest = jHist[0];
        }

        // 2. Pega o total de pacotes de verdade
        const rCount = await fetch(`${this.API}/telemetry/history?limit=10000`);
        const jCount = await rCount.json();
        this.count = jCount.length;

      } catch (e) { console.log('waiting for backend', e) }
    };
    await load();
    setInterval(load, 1000); // 1s igual ao satellite.py
  }
}
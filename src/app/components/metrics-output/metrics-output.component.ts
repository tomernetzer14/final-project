import { Component, OnInit } from '@angular/core';
import { SimplifyService } from '../../services/simplify.service';
import { Metrics } from '../../services/api.service';
import Chart from 'chart.js/auto';
import { SettingsService } from '../../services/settings.service';


@Component({
  selector: 'app-metrics-output',
  standalone: false,
  templateUrl: './metrics-output.component.html',
  styleUrl: './metrics-output.component.css'
})
export class MetricsOutputComponent implements OnInit {
  metrics: Metrics | null = null;
  chart: any;

 constructor(
    private simplifyService: SimplifyService,
    private settingsService: SettingsService,

  ) {}
  ngOnInit() {
  this.simplifyService.metrics$.subscribe(metrics => {
    this.metrics = metrics;
    setTimeout(() => {
      if (this.shouldShowMetrics()) {
        this.renderChart();
      }
    }, 0);
  });

  this.settingsService.advancedMode$.subscribe(mode => {
    if (mode === 'advanced' && this.metrics) {
      setTimeout(() => this.renderChart(), 0);
    }
  });
  }


  shouldShowMetrics(): boolean {
    return this.settingsService.getCurrentMode() === 'advanced' && !!this.metrics;
  }

  renderChart() {
    setTimeout(() => {
      if (!this.metrics) return;

      const canvas = document.getElementById('metricsChart') as HTMLCanvasElement;
      if (!canvas) return;

      if (this.chart) {
        this.chart.destroy();
      }

      const data = {
        labels: ['Readability', 'Complexity', 'Frequency', 'BERTScore','BertSim'],
        datasets: [{
          label: 'מדדים (%)',
          data: [
            this.metrics.readability,
            this.metrics.complexity,
            this.metrics.frequencyScore,
            this.metrics.bert,
            this.metrics.berts
          ],
          backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1']
        }]
      };

      const config = {
        type: 'bar' as const,
        data,
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx: any) => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}%`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100
            }
          }
        }
      };

      this.chart = new Chart(canvas, config);
    }, 0);
  }
}
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { SiemService } from '../../services/siem.service';

@Component({
  selector: 'app-metrics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './metrics.html',
  styleUrl: './metrics.css',
})
export class Metrics implements OnInit {
  private siemService = inject(SiemService);
  private cdr = inject(ChangeDetectorRef);

  metrics: any[] = [];
  total = 0;
  elapsedMs = 0;
  isLoading = false;
  error = '';
  lastUpdated = '';
  expandedRow: number | null = null;

  filters = {
    host: '',
    metric_name: '',
    limit: 100,
  };

  ngOnInit() {
    this.loadMetrics();
  }

  loadMetrics() {
    this.isLoading = true;
    this.error = '';

    this.siemService.getMetrics(this.filters).subscribe({
      next: (response) => {
        this.metrics = response.items;
        this.total = response.total;
        this.elapsedMs = response.elapsed_ms;
        this.lastUpdated = this.siemService.formatDateTime(Date.now());
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err?.error?.error || 'Metrics request failed';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  resetFilters() {
    this.filters = {
      host: '',
      metric_name: '',
      limit: 100,
    };
    this.loadMetrics();
  }

  toggleRow(index: number) {
    this.expandedRow = this.expandedRow === index ? null : index;
  }

  metricTime(metric: any): string {
    return this.siemService.formatDateTime(metric.timestamp);
  }
}

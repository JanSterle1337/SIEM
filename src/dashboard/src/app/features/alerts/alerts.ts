import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription, switchMap, timer } from 'rxjs';

import { SiemService } from '../../services/siem.service';

type AlertFilterKey = 'severity' | 'detection_type' | 'status' | 'host';

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alerts.html',
  styleUrl: './alerts.css',
})
export class Alerts implements OnInit, OnDestroy {
  private siemService = inject(SiemService);
  private cdr = inject(ChangeDetectorRef);
  private refreshSub?: Subscription;

  alerts: any[] = [];
  total = 0;
  elapsedMs = 0;
  isLoading = true;
  error = '';
  lastUpdated = '';
  expandedRow: number | null = null;
  hostOptions: string[] = [];
  severityOptions = ['critical', 'high', 'medium', 'low'];
  detectionTypeOptions = ['rule', 'anomaly', 'correlation'];
  statusOptions = ['new', 'open', 'closed', 'dismissed'];

  filters = {
    severity: '',
    detection_type: '',
    status: '',
    host: '',
    limit: 100,
  };

  ngOnInit() {
    this.setupAutoRefresh();
  }

  setupAutoRefresh() {
    this.refreshSub?.unsubscribe();
    this.isLoading = true;

    this.refreshSub = timer(0, 5000)
      .pipe(switchMap(() => this.siemService.getAlerts(this.filters)))
      .subscribe({
        next: (response) => {
          this.alerts = response.items;
          this.total = response.total;
          this.elapsedMs = response.elapsed_ms;
          this.lastUpdated = this.siemService.formatDateTime(Date.now());
          this.updateFilterOptions();
          this.isLoading = false;
          this.error = '';
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.error = err?.error?.error || 'Alerts request failed';
          this.isLoading = false;
          this.cdr.detectChanges();
        },
      });
  }

  applyFilters() {
    this.setupAutoRefresh();
  }

  resetFilters() {
    this.filters = {
      severity: '',
      detection_type: '',
      status: '',
      host: '',
      limit: 100,
    };
    this.setupAutoRefresh();
  }

  toggleRow(index: number) {
    this.expandedRow = this.expandedRow === index ? null : index;
  }

  alertTime(alert: any): string {
    return this.siemService.formatDateTime(alert.created_at || alert.timestamp);
  }

  activeFilters(): Array<{ label: string; key: AlertFilterKey }> {
    const filters: Array<{ label: string; key: AlertFilterKey }> = [
      { label: `Severity: ${this.filters.severity}`, key: 'severity' },
      { label: `Type: ${this.filters.detection_type}`, key: 'detection_type' },
      { label: `Status: ${this.filters.status}`, key: 'status' },
      { label: `Host: ${this.filters.host}`, key: 'host' },
    ];

    return filters.filter((filter) => this.filters[filter.key] !== '');
  }

  clearFilter(key: AlertFilterKey) {
    this.filters[key] = '';
    this.setupAutoRefresh();
  }

  private updateFilterOptions() {
    this.hostOptions = uniqueSorted(this.alerts.map((alert) => alert.host).filter(Boolean));
  }

  ngOnDestroy() {
    this.refreshSub?.unsubscribe();
  }
}

function uniqueSorted(values: string[]): string[] {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { SiemService } from '../../services/siem.service';

type LogFilterKey = 'query' | 'host' | 'source_type';

@Component({
  selector: 'app-logs',
  imports: [CommonModule, FormsModule],
  templateUrl: './logs.html',
  styleUrl: './logs.css',
  standalone: true,
})
export class Logs implements OnInit {
  private siemService = inject(SiemService);
  private cdr = inject(ChangeDetectorRef);

  logs: any[] = [];
  total = 0;
  elapsedMs = 0;
  isLoading = false;
  error = '';
  lastUpdated = '';
  expandedRow: number | null = null;
  hostOptions: string[] = [];
  eventClassOptions: string[] = [];

  filters = {
    query: '*',
    host: '',
    source_type: '',
    limit: 100,
  };

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    this.isLoading = true;
    this.error = '';

    this.siemService.getLogs(this.filters).subscribe({
      next: (response) => {
        this.logs = response.items;
        this.total = response.total;
        this.elapsedMs = response.elapsed_ms;
        this.lastUpdated = this.siemService.formatDateTime(Date.now());
        this.updateFilterOptions();
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err?.error?.error || 'Logs request failed';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  resetFilters() {
    this.filters = {
      query: '*',
      host: '',
      source_type: '',
      limit: 100,
    };
    this.loadLogs();
  }

  toggleRow(index: number) {
    this.expandedRow = this.expandedRow === index ? null : index;
  }

  logTime(log: any): string {
    return this.siemService.formatDateTime(log.time || log.timestamp || log.created_at);
  }

  logHost(log: any): string {
    return log.device?.hostname || log.host || log.metadata?.product?.name || '-';
  }

  logSourceIp(log: any): string {
    return log.src_endpoint?.ip || log.src_ip || '-';
  }

  activeFilters(): Array<{ label: string; key: LogFilterKey }> {
    const filters: Array<{ label: string; key: LogFilterKey }> = [
      { label: `Query: ${this.filters.query}`, key: 'query' },
      { label: `Host: ${this.filters.host}`, key: 'host' },
      { label: `Class: ${this.filters.source_type}`, key: 'source_type' },
    ];

    return filters.filter((filter) => {
      const value = this.filters[filter.key];
      return value !== '' && value !== '*';
    });
  }

  clearFilter(key: LogFilterKey) {
    this.filters[key] = key === 'query' ? '*' : '';
    this.loadLogs();
  }

  private updateFilterOptions() {
    this.hostOptions = uniqueSorted(this.logs.map((log) => this.logHost(log)).filter((host) => host !== '-'));
    this.eventClassOptions = uniqueSorted(this.logs.map((log) => log.class_name).filter(Boolean));
  }
}

function uniqueSorted(values: string[]): string[] {
  return [...new Set(values)].sort((left, right) => left.localeCompare(right));
}

import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';

import { OverviewResponse, SiemService } from '../../services/siem.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  private siemService = inject(SiemService);
  private cdr = inject(ChangeDetectorRef);

  overview?: OverviewResponse;
  isLoading = true;
  error = '';
  lastUpdated = '';

  ngOnInit() {
    this.loadOverview();
  }

  loadOverview() {
    this.isLoading = true;
    this.error = '';

    this.siemService.getOverview().subscribe({
      next: (overview) => {
        this.overview = overview;
        this.lastUpdated = this.siemService.formatDateTime(Date.now());
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err?.error?.error || 'Overview request failed';
        this.isLoading = false;
        this.cdr.detectChanges();
      },
    });
  }

  objectEntries(value: Record<string, number> | undefined): Array<{ key: string; value: number }> {
    return Object.entries(value || {}).map(([key, count]) => ({ key, value: Number(count) || 0 }));
  }

  maxValue(value: Record<string, number> | undefined): number {
    return Math.max(1, ...this.objectEntries(value).map((entry) => entry.value));
  }

  barWidth(count: number, max: number): string {
    return `${Math.max(4, Math.round((count / max) * 100))}%`;
  }

  alertTime(alert: any): string {
    return this.siemService.formatDateTime(alert.created_at || alert.timestamp);
  }
}

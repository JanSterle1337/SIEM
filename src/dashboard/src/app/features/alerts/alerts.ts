import { Component, inject, OnDestroy, OnInit, ChangeDetectorRef } from '@angular/core';
import { SiemService } from "../../services/siem.service";
import { Subscription, switchMap, timer, tap } from "rxjs";
import { DatePipe, NgForOf, NgIf } from "@angular/common";

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [DatePipe, NgForOf, NgIf],
  templateUrl: './alerts.html',
  styleUrl: './alerts.css',
})
export class Alerts implements OnInit, OnDestroy {
  private siemService = inject(SiemService);
  private cdr = inject(ChangeDetectorRef);
  private refreshSub?: Subscription;

  alerts: any[] = [];
  isLoading = true; // New loading state

  ngOnInit() {
    this.setupAutoRefresh();
  }

  setupAutoRefresh() {
    this.refreshSub?.unsubscribe();

    this.refreshSub = timer(0, 5000).pipe(
        tap(() => console.log("Polling for alerts...")),
        switchMap(() => this.siemService.getAlerts())
    ).subscribe({
      next: (data: any) => {
        // Quickwit returns { hits: [...] }. Ensure we grab the array correctly.
        this.alerts = data.hits || (Array.isArray(data) ? data : []);
        this.isLoading = false;
        this.cdr.detectChanges(); // Force UI update
        console.log("Alerts received:", this.alerts);
      },
      error: (err) => {
        console.error("SIEM API ERROR", err);
        this.isLoading = false;
      }
    });
  }

  ngOnDestroy() {
    this.refreshSub?.unsubscribe();
  }
}
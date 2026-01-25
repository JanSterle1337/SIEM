import { Component, OnInit, inject, OnDestroy } from '@angular/core';
import { SiemService } from "../../services/siem.service";
import { CommonModule } from "@angular/common";
import { Subscription, switchMap, timer } from "rxjs";

@Component({
  selector: 'app-logs',
  imports: [CommonModule],
  templateUrl: './logs.html',
  styleUrl: './logs.css', // Ensure your Tailwind imports are here or in global styles
  standalone: true,
})
export class Logs implements OnInit, OnDestroy {
  private siemService = inject(SiemService);
  private refreshSub?: Subscription;

  logs: any[] = []; // Using any[] to accommodate unclassified logs safely
  currentQuery = '*';
  expandedRow: number | null = null; // New: for the JSON dropdown

  ngOnInit() {
    this.setupAutoRefresh();
  }

  setupAutoRefresh() {
    // Unsubscribe if exists to prevent multiple timers when searching
    this.refreshSub?.unsubscribe();

    this.refreshSub = timer(0, 5000).pipe(
        switchMap(() => this.siemService.getLogs(this.currentQuery))
    ).subscribe({
      next: (data: any) => {
        // Quickwit search usually returns { hits: [], num_hits: X }
        // Adjust this if your Rust API sends the hits array directly
        this.logs = data.hits || data;
      },
      error: (err) => console.error("SIEM API Error:", err)
    });
  }

  ngOnDestroy() {
    this.refreshSub?.unsubscribe();
  }

  onSearch(event: any) {
    const input = event.target as HTMLInputElement;
    this.currentQuery = input.value || '*';
    this.expandedRow = null; // Close any open JSON views on new search
    this.setupAutoRefresh(); // Restart timer to get immediate results for new query
  }

  toggleRow(index: number) {
    this.expandedRow = this.expandedRow === index ? null : index;
  }
}

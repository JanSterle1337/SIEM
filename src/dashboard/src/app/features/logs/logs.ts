import { Component, OnInit, inject } from '@angular/core';
import { SiemService } from "../../services/siem.service";
import { CommonModule } from "@angular/common";

@Component({
  selector: 'app-logs',
  imports: [CommonModule],
  templateUrl: './logs.html',
  styleUrl: './logs.css',
  standalone: true,
})
export class Logs implements OnInit {
  private siemService = inject(SiemService);

  logs: any[] = [];
  currentQuery = '*';
  expandedRow: number | null = null;

  ngOnInit() {
    // Just one plain request when the component starts
    this.loadLogs();
  }

  loadLogs() {
    this.siemService.getLogs(this.currentQuery).subscribe({
      next: (data: any) => {
        this.logs = data.hits || data;
      },
      error: (err) => console.error("API Error:", err)
    });
  }

  onSearch(event: any) {
    const input = event.target as HTMLInputElement;
    this.currentQuery = input.value || '*';
    this.loadLogs(); // Manually trigger the API call on Enter
  }

  toggleRow(index: number) {
    this.expandedRow = this.expandedRow === index ? null : index;
  }
}
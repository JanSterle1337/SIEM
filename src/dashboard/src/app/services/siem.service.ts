import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ApiListResponse<T = any> {
  items: T[];
  total: number;
  elapsed_ms: number;
}

export interface LogsFilters {
  query?: string;
  host?: string;
  source_type?: string;
  limit?: number;
}

export interface MetricsFilters {
  host?: string;
  metric_name?: string;
  limit?: number;
}

export interface AlertsFilters {
  query?: string;
  severity?: string;
  detection_type?: string;
  status?: string;
  host?: string;
  limit?: number;
}

export interface OverviewResponse {
  alert_count: number;
  alerts_by_severity: Record<string, number>;
  alerts_by_type: Record<string, number>;
  top_hosts: Array<{ host: string; count: number }>;
  recent_alerts: any[];
  event_counts: Record<string, number>;
}

@Injectable({ providedIn: 'root' })
export class SiemService {
  private http = inject(HttpClient);
  private apiUrl = '/api';

  getLogs(filters: LogsFilters = {}): Observable<ApiListResponse> {
    return this.http.get<ApiListResponse>(`${this.apiUrl}/logs`, {
      params: this.toParams(filters),
    });
  }

  getMetrics(filters: MetricsFilters = {}): Observable<ApiListResponse> {
    return this.http.get<ApiListResponse>(`${this.apiUrl}/metrics`, {
      params: this.toParams(filters),
    });
  }

  getAlerts(filters: AlertsFilters = {}): Observable<ApiListResponse> {
    return this.http.get<ApiListResponse>(`${this.apiUrl}/alerts`, {
      params: this.toParams(filters),
    });
  }

  getOverview(): Observable<OverviewResponse> {
    return this.http.get<OverviewResponse>(`${this.apiUrl}/overview`);
  }

  formatDateTime(value: unknown): string {
    if (value === undefined || value === null || value === '') {
      return '-';
    }

    let date: Date;

    if (typeof value === 'number') {
      date = new Date(value < 10_000_000_000 ? value * 1000 : value);
    } else {
      const raw = String(value);
      const normalized = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(raw)
        ? `${raw}Z`
        : raw;
      date = new Date(normalized);
    }

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    const pad = (part: number, size = 2) => String(part).padStart(size, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(date.getMilliseconds(), 3)}`;
  }

  private toParams(filters: object): HttpParams {
    let params = new HttpParams();

    for (const [key, value] of Object.entries(filters) as Array<[string, string | number | undefined]>) {
      if (value === undefined || value === null || value === '') {
        continue;
      }

      params = params.set(key, String(value));
    }

    return params;
  }
}

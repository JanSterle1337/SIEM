import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, map } from "rxjs";
import { OcsfLog } from "../models/OcsfLog";
import { SiemAlert } from "../models/SiemAlert";


@Injectable({ providedIn: 'root' })
export class SiemService {
    private http = inject(HttpClient);
    private apiUrl = 'http://localhost:3000/api';

    getLogs(query: string = '*'): Observable<OcsfLog[]> {
        return this.http.get<any>(`${this.apiUrl}/logs?query=${query}`).pipe(
            map(res => res.hits)
        );
    }

    getAlerts(): Observable<SiemAlert[]> {
        return this.http.get<any>(`${this.apiUrl}/alerts`).pipe(
            map(res => res.hits)
        )
    }

}
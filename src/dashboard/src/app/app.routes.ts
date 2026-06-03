import { Routes } from '@angular/router';
import { Logs } from "./features/logs/logs";
import {Dashboard} from "./features/dashboard/dashboard";
import {Alerts} from "./features/alerts/alerts";
import {Metrics} from "./features/metrics/metrics";


export const routes: Routes = [
    { path: 'logs', component: Logs },
    { path: 'metrics', component: Metrics },
    { path: 'alerts', component: Alerts },
    { path: 'dashboard', component: Dashboard },
    { path: '', redirectTo: '/dashboard', pathMatch: 'full'},
    { path: '**', redirectTo: '/dashboard' }
];

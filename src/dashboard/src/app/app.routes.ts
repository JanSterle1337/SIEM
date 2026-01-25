import { Routes } from '@angular/router';
import { Logs } from "./features/logs/logs";
import {Dashboard} from "./features/dashboard/dashboard";
import {Alerts} from "./features/alerts/alerts";


export const routes: Routes = [
    { path: 'logs', component: Logs },
    { path: 'alerts', component: Alerts },
    { path: 'dashboard', component: Dashboard },
    { path: '', redirectTo: '/dashboard', pathMatch: 'full'},
    { path: '**', redirectTo: '/dashboard' }
];

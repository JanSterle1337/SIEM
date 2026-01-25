import { Routes } from '@angular/router';
import { Logs } from "./features/logs/logs";
import {Dashboard} from "./features/dashboard/dashboard";


export const routes: Routes = [
    { path: 'logs', component: Logs },
    { path: 'dashboard', component: Dashboard },
    { path: '', redirectTo: '/dashboard', pathMatch: 'full'},
    { path: '**', redirectTo: '/dashboard' }
];

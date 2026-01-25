export interface SiemAlert {
    alert_type: string;
    severity: 'High' | 'Medium' | 'Low';
    source_ip: string,
    msg: string,
    timestamp: number;
}
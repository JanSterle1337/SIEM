export interface OcsfLog {
    time: number;
    category_uid: number;
    class_uid: number;
    message: string;
    src_endpoint?: { ip: string };
    metadata: { product: { name: string } };
}
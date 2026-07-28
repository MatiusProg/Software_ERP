/*
  Tipos que reflejan lo que devuelve la API. Los importes llegan como *string*
  (DRF serializa Decimal así, a propósito, para no perder precisión en JSON):
  se convierten con Number() solo para mostrar o sumar en pantalla.
*/

export interface Pagina<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type Rol = "propietario" | "admin" | "vendedor" | "lectura";

export interface Membresia {
  id: number;
  rol: Rol;
  organizacion: { id: string; nombre: string; slug: string; activa: boolean };
}

export interface Yo {
  id: number;
  email: string;
  nombre_completo: string;
  membresias: Membresia[];
  organizacion_activa: string | null;
  rol_activo: Rol | null;
}

export interface Categoria {
  id: number;
  nombre: string;
  descripcion: string;
}

export interface Producto {
  id: number;
  sku: string;
  codigo_barras: string;
  nombre: string;
  categoria: number | null;
  categoria_nombre?: string;
  unidad: string;
  es_servicio: boolean;
  precio_venta: string;
  precio_venta_minimo: string;
  precio_compra: string;
  precio_compra_maximo: string;
  stock: string;
  impuesto: string;
  activo: boolean;
}

export interface Contacto {
  id?: number;
  tipo: "telefono" | "email" | "whatsapp" | string;
  valor: string;
}

export interface Tercero {
  id: number;
  nombre: string;
  nit_ci: string;
  es_cliente: boolean;
  es_proveedor: boolean;
  es_transportadora: boolean;
  notas: string;
  activo: boolean;
  contactos: Contacto[];
  ubicaciones: unknown[];
}

/** Línea de venta/cotización/lista. `cantidad` y `precio_unitario` solo van en
 *  el modo unitario; en el modo directo se manda `total` a secas. */
export interface Linea {
  id?: number;
  producto: number | null;
  descripcion: string;
  detalle: string;
  cantidad: string | null;
  precio_unitario: string | null;
  impuesto?: string;
  impuesto_monto?: string;
  total: string;
  orden?: number;
  comprado?: boolean;
}

interface DocumentoBase {
  id: number;
  cliente: number | null;
  cliente_nombre: string;
  estado: string;
  estado_display: string;
  notas: string;
  total: string;
  creado_en: string;
  actualizado_en: string;
}

export interface Venta extends DocumentoBase {
  numero: string;
  estado_pago: "pendiente" | "parcial" | "pagado";
  estado_pago_display: string;
  cotizacion_origen: number | null;
  subtotal: string;
  impuesto_total: string;
  detalles: Linea[];
  /** Nota pública por QR (ver apps/ventas/publico.py en el backend). */
  token_publico: string;
  url_publica: string;
  url_qr: string;
}

export interface Cotizacion extends DocumentoBase {
  numero: string;
  validez_dias: number;
  subtotal: string;
  impuesto_total: string;
  detalles: Linea[];
}

export interface Lista extends DocumentoBase {
  titulo: string;
  items: Linea[];
}

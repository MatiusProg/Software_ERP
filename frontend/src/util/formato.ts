/** Formatos de presentación. La moneda es fija (Bolivia) hasta que exista un
 *  campo `moneda` en la organización. */

export const MONEDA = "Bs";

export const dinero = (valor: string | number | null | undefined) =>
  `${MONEDA} ${Number(valor ?? 0).toFixed(2)}`;

/** "15.000" -> "15" · "0.500" -> "0.5" */
export const cantidad = (valor: string | number | null | undefined) =>
  valor === null || valor === undefined || valor === "" ? "" : String(parseFloat(String(valor)));

export const fecha = (iso: string) =>
  new Date(iso).toLocaleString("es-BO", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export const fechaCorta = (iso: string) =>
  new Date(iso).toLocaleDateString("es-BO", { day: "2-digit", month: "short" });

/** IVA contenido en un precio (los precios se manejan IVA incluido). */
export function impuestoContenido(total: number, tasa: number) {
  if (!tasa) return 0;
  return (total * tasa) / (100 + tasa);
}

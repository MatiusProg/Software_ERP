/*
  Editor de líneas compartido por venta, cotización y lista.

  Es el mismo modelo que el backend (ver apps/ventas/models.py):
  - **modo directo** (por defecto): se escribe el total de la línea;
  - **modo unitario** (opt-in por línea, botón ×): cantidad × precio unitario.

  Los totales que se calculan aquí son solo para que el usuario *vea* lo que va
  cobrando. Los definitivos los devuelve el backend al guardar — no se duplica
  la regla del IVA en dos lugares.
*/

import type { Producto } from "../api/tipos";
import { apiProductos } from "../api/recursos";
import { cantidad, impuestoContenido, dinero } from "../util/formato";
import { Autocompletar } from "./Autocompletar";

export interface LineaEditable {
  clave: string;
  producto: number | null;
  descripcion: string;
  detalle: string;
  modoUnitario: boolean;
  cantidad: string;
  precioUnitario: string;
  total: string;
  impuesto: string;
  /** Precio mínimo de venta del producto (vacío en líneas de texto libre). */
  minimo: string;
  comprado?: boolean;
}

let contador = 0;
export function nuevaLinea(datos: Partial<LineaEditable> = {}): LineaEditable {
  contador += 1;
  return {
    clave: `l${contador}`,
    producto: null,
    descripcion: "",
    detalle: "",
    modoUnitario: false,
    cantidad: "1",
    precioUnitario: "",
    total: "",
    impuesto: "13",
    minimo: "",
    ...datos,
  };
}

export function lineaDesdeProducto(p: Producto): LineaEditable {
  return nuevaLinea({
    producto: p.id,
    descripcion: p.nombre,
    modoUnitario: true,
    cantidad: "1",
    precioUnitario: p.precio_venta,
    impuesto: p.impuesto,
    minimo: p.precio_venta_minimo,
  });
}

export function totalLinea(l: LineaEditable): number {
  if (l.modoUnitario) return (Number(l.cantidad) || 0) * (Number(l.precioUnitario) || 0);
  return Number(l.total) || 0;
}

/**
 * Precio por unidad que representa la línea. Espeja el cálculo del backend
 * (`precio_efectivo` en apps/ventas/serializers.py): sin cantidad se asume una
 * unidad, que es lo conservador.
 */
export function precioEfectivo(l: LineaEditable): number {
  if (l.modoUnitario) return Number(l.precioUnitario) || 0;
  return (Number(l.total) || 0) / (Number(l.cantidad) || 1);
}

export function bajoMinimo(l: LineaEditable): boolean {
  const minimo = Number(l.minimo) || 0;
  return !!l.producto && minimo > 0 && precioEfectivo(l) < minimo;
}

/** Avisos para confirmar antes de guardar (uno por línea bajo el piso). */
export function avisosBajoMinimo(lineas: LineaEditable[]): string[] {
  return lineas
    .filter(bajoMinimo)
    .map((l) => `${l.descripcion}: ${dinero(precioEfectivo(l))} — el mínimo es ${dinero(l.minimo)}`);
}

/** Totales del documento, con el IVA ya contenido en los precios. */
export function totalesDe(lineas: LineaEditable[], fiscal: boolean) {
  const total = lineas.reduce((suma, l) => suma + totalLinea(l), 0);
  const impuesto = fiscal
    ? lineas.reduce((suma, l) => suma + impuestoContenido(totalLinea(l), Number(l.impuesto) || 0), 0)
    : 0;
  return { total, impuesto, subtotal: total - impuesto };
}

/** Traduce las líneas al formato que espera la API. */
export function lineasAPayload(lineas: LineaEditable[], fiscal: boolean) {
  return lineas
    .filter((l) => l.descripcion.trim() || l.producto)
    .map((l, i) => {
      const base: Record<string, unknown> = {
        producto: l.producto,
        descripcion: l.descripcion.trim(),
        detalle: l.detalle.trim(),
        orden: i,
      };
      if (l.modoUnitario) {
        base.cantidad = l.cantidad || "0";
        base.precio_unitario = l.precioUnitario || "0";
      } else {
        base.total = l.total || "0";
      }
      if (fiscal) base.impuesto = l.impuesto || "0";
      if (l.comprado !== undefined) base.comprado = l.comprado;
      return base;
    });
}

interface Props {
  lineas: LineaEditable[];
  setLineas: (l: LineaEditable[]) => void;
  fiscal: boolean;
  /** Las listas de la PWA marcan lo ya comprado. */
  conComprado?: boolean;
  refBuscador?: React.RefObject<HTMLInputElement | null>;
}

export function EditorLineas({ lineas, setLineas, fiscal, conComprado, refBuscador }: Props) {
  const cambiar = (clave: string, cambios: Partial<LineaEditable>) =>
    setLineas(lineas.map((l) => (l.clave === clave ? { ...l, ...cambios } : l)));

  const agregar = (l: LineaEditable) => setLineas([...lineas, l]);
  const quitar = (clave: string) => setLineas(lineas.filter((l) => l.clave !== clave));

  return (
    <div>
      <Autocompletar<Producto>
        refExterna={refBuscador}
        autoFocus
        placeholder="Buscar producto por nombre, SKU o código… (Enter agrega; texto libre también sirve)"
        buscar={async (texto) =>
          (await apiProductos.listar({ search: texto, activo: true })).results.slice(0, 8)
        }
        pintar={(p) => (
          <>
            <span>
              <strong>{p.nombre}</strong>
              {p.sku && <span style={{ color: "var(--tenue)" }}> · {p.sku}</span>}
            </span>
            <span className="num">{dinero(p.precio_venta)}</span>
          </>
        )}
        alElegir={(p) => {
          // Si el producto ya está en la nota, se suma una unidad en vez de repetirlo.
          const existente = lineas.find((l) => l.producto === p.id && l.modoUnitario);
          if (existente) {
            cambiar(existente.clave, { cantidad: String((Number(existente.cantidad) || 0) + 1) });
          } else {
            agregar(lineaDesdeProducto(p));
          }
        }}
        alTextoLibre={(texto) => agregar(nuevaLinea({ descripcion: texto }))}
      />

      <div style={{ marginTop: 14 }}>
        {lineas.length === 0 && (
          <p style={{ color: "var(--tenue)", fontSize: 14 }}>
            Busca un producto o escribe cualquier cosa y pulsa Enter para agregarla a mano.
          </p>
        )}

        {lineas.map((l) => (
          <div className={`linea-pos${bajoMinimo(l) ? " alerta" : ""}`} key={l.clave}>
            <div>
              <input
                className="desc-input"
                value={l.descripcion}
                placeholder="Descripción"
                onChange={(e) => cambiar(l.clave, { descripcion: e.target.value })}
              />
              <input
                style={{ marginTop: 4, fontSize: 13 }}
                value={l.detalle}
                placeholder="Detalle (1 java, 1/4, caja…)"
                onChange={(e) => cambiar(l.clave, { detalle: e.target.value })}
              />
            </div>

            {l.modoUnitario ? (
              <>
                <input
                  className="num"
                  inputMode="decimal"
                  value={l.cantidad}
                  title="Cantidad"
                  onChange={(e) => cambiar(l.clave, { cantidad: e.target.value })}
                />
                <input
                  className="num"
                  inputMode="decimal"
                  value={l.precioUnitario}
                  title="Precio unitario"
                  onChange={(e) => cambiar(l.clave, { precioUnitario: e.target.value })}
                />
              </>
            ) : (
              <>
                <button
                  className="plano"
                  title="Cambiar a cantidad × precio unitario"
                  onClick={() =>
                    cambiar(l.clave, {
                      modoUnitario: true,
                      cantidad: "1",
                      precioUnitario: l.total || "",
                    })
                  }
                >
                  × unidad
                </button>
                <input
                  className="num"
                  inputMode="decimal"
                  value={l.total}
                  placeholder="Total"
                  title="Total de la línea"
                  onChange={(e) => cambiar(l.clave, { total: e.target.value })}
                />
              </>
            )}

            <div className="num" style={{ fontWeight: 700 }}>
              {dinero(totalLinea(l))}
              {bajoMinimo(l) ? (
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--peligro)" }}>
                  bajo el mín. {dinero(l.minimo)}
                </div>
              ) : (
                fiscal &&
                Number(l.impuesto) > 0 && (
                  <div style={{ fontSize: 11, fontWeight: 400, color: "var(--tenue)" }}>
                    IVA {cantidad(l.impuesto)}% incl.
                  </div>
                )
              )}
              {l.modoUnitario && (
                <button
                  className="plano"
                  style={{ fontSize: 11, padding: "1px 5px", display: "block", marginLeft: "auto" }}
                  title="Volver a escribir el total directo"
                  onClick={() =>
                    cambiar(l.clave, { modoUnitario: false, total: totalLinea(l).toFixed(2) })
                  }
                >
                  total directo
                </button>
              )}
            </div>

            <div className="fila" style={{ gap: 4 }}>
              {conComprado && (
                <input
                  type="checkbox"
                  checked={!!l.comprado}
                  title="Comprado"
                  onChange={(e) => cambiar(l.clave, { comprado: e.target.checked })}
                />
              )}
              <button className="plano icono" title="Quitar" onClick={() => quitar(l.clave)}>
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      <button className="plano" style={{ marginTop: 10 }} onClick={() => agregar(nuevaLinea())}>
        + Línea en blanco
      </button>
    </div>
  );
}

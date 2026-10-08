/*
  Historial de ventas: buscar una nota, ver su detalle, cambiar el estado de
  pago y volver a mostrar su QR (por si el cliente perdió la nota).
*/

import { useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiVentas, useLista } from "../api/recursos";
import type { Venta } from "../api/tipos";
import { useSesion } from "../auth/sesion";
import { NotaQR } from "../componentes/NotaQR";
import { Cargando, ChipEstado, Error, Modal, Vacio } from "../componentes/ui";
import { cantidad, dinero, fecha } from "../util/formato";

export function Ventas() {
  const { permisos } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const [estadoPago, setEstadoPago] = useState("");
  const [soloBajoMinimo, setSoloBajoMinimo] = useState(false);
  const [abierta, setAbierta] = useState<Venta | null>(null);
  const [error, setError] = useState("");

  const { datos, total, cargando, recargar } = useLista<Venta>("/ventas/", {
    search: busqueda || undefined,
    estado_pago: estadoPago || undefined,
    bajo_minimo: soloBajoMinimo || undefined,
  });

  async function marcarPagada(venta: Venta) {
    try {
      const actualizada = await apiVentas.actualizar(venta.id, { estado_pago: "pagado" });
      setAbierta(actualizada);
      await recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Ventas</h1>
          <p>{total} notas emitidas</p>
        </div>
        <div className="fila">
          <input
            style={{ width: 240 }}
            placeholder="Buscar por número o cliente…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <select style={{ width: 170 }} value={estadoPago} onChange={(e) => setEstadoPago(e.target.value)}>
            <option value="">Todos los cobros</option>
            <option value="pagado">Pagadas</option>
            <option value="pendiente">Pendientes</option>
            <option value="parcial">Parciales</option>
          </select>
          <label className="fila" style={{ gap: 6, fontSize: 13 }}>
            <input
              type="checkbox"
              checked={soloBajoMinimo}
              onChange={(e) => setSoloBajoMinimo(e.target.checked)}
            />
            Bajo el mínimo
          </label>
        </div>
      </div>

      <Error>{error}</Error>

      <div className="tarjeta tabla-caja">
        {cargando ? (
          <Cargando />
        ) : datos.length === 0 ? (
          <Vacio titulo="Todavía no hay ventas">
            Emite la primera desde <strong>Punto de venta</strong>.
          </Vacio>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Número</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Cobro</th>
                <th className="num">Total</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {datos.map((v) => (
                <tr key={v.id} className="clic" onClick={() => setAbierta(v)}>
                  <td className="t-principal">
                    <strong>{v.numero}</strong>
                  </td>
                  <td className="t-sec" style={{ color: "var(--tenue)" }}>{fecha(v.creado_en)}</td>
                  <td className="t-sec">
                    {v.cliente_nombre || "—"}
                    {v.bajo_minimo && (
                      <span className="chip mal" style={{ marginLeft: 6 }} title="Se autorizó vender por debajo del precio mínimo">
                        bajo mín.
                      </span>
                    )}
                  </td>
                  <td className="t-sec">
                    {v.estado === "anulada" ? (
                      <ChipEstado estado="anulada" texto="Anulada" />
                    ) : (
                      <ChipEstado estado={v.estado_pago} texto={v.estado_pago_display} />
                    )}
                  </td>
                  <td className="num t-monto">
                    <strong>{dinero(v.total)}</strong>
                  </td>
                  <td className="num t-accion">
                    <button
                      className="plano"
                      onClick={(e) => {
                        e.stopPropagation();
                        setAbierta(v);
                      }}
                    >
                      Ver QR
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {abierta && (
        <Modal titulo={`Nota ${abierta.numero}`} ancho={640} onCerrar={() => setAbierta(null)}>
          <div className="fila" style={{ justifyContent: "space-between" }}>
            <span style={{ color: "var(--tenue)" }}>{fecha(abierta.creado_en)}</span>
            <ChipEstado estado={abierta.estado_pago} texto={abierta.estado_pago_display} />
          </div>
          <p style={{ marginBottom: 4 }}>
            Cliente: <strong>{abierta.cliente_nombre || "Consumidor final"}</strong>
          </p>

          <div className="tabla-caja" style={{ border: "1px solid var(--borde)", marginTop: 10 }}>
            <table>
              <tbody>
                {abierta.detalles.map((d, i) => (
                  <tr key={i}>
                    <td>
                      {d.descripcion}
                      {(d.detalle || d.cantidad) && (
                        <div style={{ fontSize: 12, color: "var(--tenue)" }}>
                          {d.detalle}
                          {d.detalle && d.cantidad ? " · " : ""}
                          {d.cantidad && `${cantidad(d.cantidad)} × ${dinero(d.precio_unitario)}`}
                        </div>
                      )}
                    </td>
                    <td className="num">{dinero(d.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="fila" style={{ justifyContent: "space-between", marginTop: 12 }}>
            <span style={{ fontWeight: 700 }}>TOTAL</span>
            <span style={{ fontWeight: 800, fontSize: 22 }}>{dinero(abierta.total)}</span>
          </div>
          <div style={{ fontSize: 12, color: "var(--tenue)", textAlign: "right" }}>
            IVA incluido {dinero(abierta.impuesto_total)}
          </div>

          {permisos.puedeVender && abierta.estado_pago !== "pagado" && (
            <button style={{ marginTop: 12 }} onClick={() => marcarPagada(abierta)}>
              Marcar como pagada
            </button>
          )}

          <hr style={{ border: 0, borderTop: "1px solid var(--borde)", margin: "16px 0" }} />
          <NotaQR venta={abierta} />
        </Modal>
      )}
    </>
  );
}

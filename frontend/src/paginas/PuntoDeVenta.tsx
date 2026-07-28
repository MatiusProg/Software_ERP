/*
  Punto de venta — la pantalla central del panel.

  Flujo: buscar producto (o escribir a mano) → armar las líneas → elegir cliente
  (opcional) → Cobrar. Al guardar, el backend asigna el número correlativo y
  devuelve la venta con su QR: se muestra al instante para que el cliente lo
  escanee y se lleve su nota.

  Los totales de la izquierda son una vista previa; los definitivos vienen del
  backend (el IVA se calcula en un solo lugar).
*/

import { useEffect, useRef, useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiVentas } from "../api/recursos";
import type { Tercero, Venta } from "../api/tipos";
import { useSesion } from "../auth/sesion";
import { NotaQR } from "../componentes/NotaQR";
import { SelectorCliente } from "../componentes/SelectorCliente";
import {
  EditorLineas,
  lineasAPayload,
  totalesDe,
  type LineaEditable,
} from "../componentes/lineas";
import { Campo, Error, Modal } from "../componentes/ui";
import { dinero } from "../util/formato";

export function PuntoDeVenta() {
  const { permisos } = useSesion();
  const [lineas, setLineas] = useState<LineaEditable[]>([]);
  const [cliente, setCliente] = useState<Tercero | null>(null);
  const [nombreLibre, setNombreLibre] = useState("");
  const [estadoPago, setEstadoPago] = useState("pagado");
  const [notas, setNotas] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [emitida, setEmitida] = useState<Venta | null>(null);
  const buscador = useRef<HTMLInputElement>(null);

  const { total, impuesto, subtotal } = totalesDe(lineas, true);

  // F2 devuelve el cursor al buscador sin soltar el teclado.
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "F2") {
        e.preventDefault();
        buscador.current?.focus();
      }
    };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, []);

  function limpiar() {
    setLineas([]);
    setCliente(null);
    setNombreLibre("");
    setNotas("");
    setEstadoPago("pagado");
    setError("");
    buscador.current?.focus();
  }

  async function cobrar() {
    if (!lineas.length) return;
    setGuardando(true);
    setError("");
    try {
      const venta = await apiVentas.crear({
        cliente: cliente?.id ?? null,
        cliente_nombre: cliente ? "" : nombreLibre.trim(),
        estado_pago: estadoPago,
        notas: notas.trim(),
        detalles: lineasAPayload(lineas, true),
      });
      setEmitida(venta);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  if (!permisos.puedeVender) {
    return (
      <div className="tarjeta pad">
        Tu rol es de solo lectura: puedes consultar, pero no emitir ventas.
      </div>
    );
  }

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Punto de venta</h1>
          <p>Enter agrega lo buscado · F2 vuelve al buscador · el QR sale al cobrar</p>
        </div>
        {lineas.length > 0 && (
          <button className="plano" onClick={limpiar}>
            Descartar
          </button>
        )}
      </div>

      <div className="pos">
        <div className="tarjeta pad">
          <EditorLineas lineas={lineas} setLineas={setLineas} fiscal refBuscador={buscador} />
        </div>

        <div className="tarjeta pad resumen">
          <Campo etiqueta="Cliente">
            <SelectorCliente
              cliente={cliente}
              setCliente={setCliente}
              nombreLibre={nombreLibre}
              setNombreLibre={setNombreLibre}
            />
          </Campo>

          <Campo etiqueta="Cobro">
            <select value={estadoPago} onChange={(e) => setEstadoPago(e.target.value)}>
              <option value="pagado">Pagado</option>
              <option value="pendiente">Pendiente (fiado)</option>
              <option value="parcial">Pago parcial</option>
            </select>
          </Campo>

          <Campo etiqueta="Notas (salen en la nota)">
            <textarea value={notas} onChange={(e) => setNotas(e.target.value)} rows={2} />
          </Campo>

          <hr style={{ border: 0, borderTop: "1px solid var(--borde)", margin: "14px 0" }} />

          <div className="fila" style={{ justifyContent: "space-between", color: "var(--tenue)", fontSize: 14 }}>
            <span>Subtotal</span>
            <span className="num">{dinero(subtotal)}</span>
          </div>
          <div className="fila" style={{ justifyContent: "space-between", color: "var(--tenue)", fontSize: 14 }}>
            <span>IVA incluido</span>
            <span className="num">{dinero(impuesto)}</span>
          </div>
          <div className="fila" style={{ justifyContent: "space-between", marginTop: 8 }}>
            <span style={{ fontWeight: 700 }}>TOTAL</span>
            <span className="total-grande">{dinero(total)}</span>
          </div>

          <Error>{error}</Error>

          <button
            className="primario grande"
            style={{ marginTop: 14 }}
            disabled={!lineas.length || guardando}
            onClick={cobrar}
          >
            {guardando ? "Emitiendo…" : `Cobrar ${dinero(total)}`}
          </button>
        </div>
      </div>

      {emitida && (
        <Modal
          titulo={`Nota ${emitida.numero} emitida`}
          ancho={620}
          onCerrar={() => {
            setEmitida(null);
            limpiar();
          }}
          pie={
            <button
              className="primario"
              onClick={() => {
                setEmitida(null);
                limpiar();
              }}
            >
              Nueva venta
            </button>
          }
        >
          <p style={{ marginTop: 0 }}>
            Total cobrado <strong>{dinero(emitida.total)}</strong>
            {emitida.cliente_nombre && <> · {emitida.cliente_nombre}</>}
          </p>
          <NotaQR venta={emitida} cliente={cliente} />
        </Modal>
      )}
    </>
  );
}

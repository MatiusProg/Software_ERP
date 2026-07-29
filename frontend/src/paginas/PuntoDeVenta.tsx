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
  avisosBajoMinimo,
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
  const [porConfirmar, setPorConfirmar] = useState<string[] | null>(null);
  const buscador = useRef<HTMLInputElement>(null);

  const { total, impuesto, subtotal } = totalesDe(lineas, true);
  const avisos = avisosBajoMinimo(lineas);

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

  /**
   * Emite la venta. Si hay líneas por debajo del precio mínimo, primero pide
   * confirmación: el backend también las rechaza, así que el aviso de aquí es
   * para no hacer ir y volver al vendedor, no la única defensa.
   */
  async function cobrar(autorizado = false) {
    if (!lineas.length) return;
    if (!autorizado && avisos.length) {
      setPorConfirmar(avisos);
      return;
    }
    setGuardando(true);
    setError("");
    try {
      const venta = await apiVentas.crear({
        cliente: cliente?.id ?? null,
        cliente_nombre: cliente ? "" : nombreLibre.trim(),
        estado_pago: estadoPago,
        notas: notas.trim(),
        autorizar_precio_bajo: autorizado,
        detalles: lineasAPayload(lineas, true),
      });
      setPorConfirmar(null);
      setEmitida(venta);
    } catch (e) {
      // Por si el backend detecta un caso que el panel no vio (precios que
      // cambiaron mientras se armaba la venta).
      const datos = (e as { response?: { data?: { precio_bajo_minimo?: string[] } } })
        .response?.data;
      if (datos?.precio_bajo_minimo) setPorConfirmar(datos.precio_bajo_minimo);
      else setError(mensajeDeError(e));
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

          {avisos.length > 0 && (
            <div className="error" style={{ marginTop: 12 }}>
              {avisos.length === 1
                ? "1 producto va por debajo de su precio mínimo."
                : `${avisos.length} productos van por debajo de su precio mínimo.`}{" "}
              Se pedirá confirmación al cobrar.
            </div>
          )}

          <button
            className="primario grande"
            style={{ marginTop: 14 }}
            disabled={!lineas.length || guardando}
            onClick={() => cobrar()}
          >
            {guardando ? "Emitiendo…" : `Cobrar ${dinero(total)}`}
          </button>
        </div>
      </div>

      {porConfirmar && (
        <Modal
          titulo="Vas a vender por debajo del mínimo"
          onCerrar={() => setPorConfirmar(null)}
          pie={
            <>
              <button onClick={() => setPorConfirmar(null)}>Revisar precios</button>
              <button className="primario" disabled={guardando} onClick={() => cobrar(true)}>
                {guardando ? "Emitiendo…" : "Autorizar y cobrar"}
              </button>
            </>
          }
        >
          <p style={{ marginTop: 0 }}>
            Estos precios están por debajo del piso que fijaste en el catálogo:
          </p>
          <ul style={{ paddingLeft: 18, lineHeight: 1.8 }}>
            {porConfirmar.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
          <p style={{ color: "var(--tenue)", fontSize: 13, marginBottom: 0 }}>
            Si autorizas, la venta se emite igual y queda <strong>marcada</strong> para
            que puedas revisarla después (filtro «bajo el mínimo» en Ventas).
          </p>
        </Modal>
      )}

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

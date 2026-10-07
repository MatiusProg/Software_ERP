/*
  Cotizaciones: mismo editor de líneas que el punto de venta, más el botón que
  las convierte en venta (el backend copia las líneas, congela los precios y
  marca la cotización como aceptada).
*/

import { useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiCotizaciones, useLista } from "../api/recursos";
import type { Cotizacion, Tercero, Venta } from "../api/tipos";
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
import { Campo, Cargando, ChipEstado, Error, Modal, Vacio } from "../componentes/ui";
import { dinero, fecha } from "../util/formato";

export function Cotizaciones() {
  const { permisos } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const [creando, setCreando] = useState(false);
  const [abierta, setAbierta] = useState<Cotizacion | null>(null);
  const [convertida, setConvertida] = useState<Venta | null>(null);
  const [error, setError] = useState("");

  const { datos, total, cargando, recargar } = useLista<Cotizacion>("/cotizaciones/", {
    search: busqueda || undefined,
  });

  async function convertir(cotizacion: Cotizacion) {
    setError("");
    try {
      const venta = await apiCotizaciones.convertirEnVenta(cotizacion.id);
      setAbierta(null);
      setConvertida(venta);
      await recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Cotizaciones</h1>
          <p>{total} en total</p>
        </div>
        <div className="fila">
          <input
            style={{ width: 230 }}
            placeholder="Buscar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          {permisos.puedeVender && (
            <button className="primario" onClick={() => setCreando(true)}>
              Nueva cotización
            </button>
          )}
        </div>
      </div>

      <Error>{error}</Error>

      <div className="tarjeta tabla-caja">
        {cargando ? (
          <Cargando />
        ) : datos.length === 0 ? (
          <Vacio titulo="Sin cotizaciones">Crea una para pasarle precios a un cliente.</Vacio>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Número</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Estado</th>
                <th className="num">Total</th>
              </tr>
            </thead>
            <tbody>
              {datos.map((c) => (
                <tr key={c.id} className="clic" onClick={() => setAbierta(c)}>
                  <td className="t-principal">
                    <strong>{c.numero}</strong>
                  </td>
                  <td className="t-sec" style={{ color: "var(--tenue)" }}>{fecha(c.creado_en)}</td>
                  <td className="t-sec">{c.cliente_nombre || "—"}</td>
                  <td className="t-sec">
                    <ChipEstado estado={c.estado} texto={c.estado_display} />
                  </td>
                  <td className="num t-monto">
                    <strong>{dinero(c.total)}</strong>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {creando && (
        <EditorCotizacion
          onCerrar={() => setCreando(false)}
          onGuardada={async () => {
            setCreando(false);
            await recargar();
          }}
        />
      )}

      {abierta && (
        <Modal titulo={`Cotización ${abierta.numero}`} onCerrar={() => setAbierta(null)}>
          <p style={{ marginTop: 0, color: "var(--tenue)" }}>
            {fecha(abierta.creado_en)} · válida {abierta.validez_dias} días
          </p>
          <p>
            Cliente: <strong>{abierta.cliente_nombre || "—"}</strong>
          </p>
          <table>
            <tbody>
              {abierta.detalles.map((d, i) => (
                <tr key={i}>
                  <td>{d.descripcion}</td>
                  <td className="num">{dinero(d.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="fila" style={{ justifyContent: "space-between", marginTop: 12 }}>
            <strong>TOTAL</strong>
            <span style={{ fontWeight: 800, fontSize: 20 }}>{dinero(abierta.total)}</span>
          </div>
          {permisos.puedeVender && abierta.estado !== "aceptada" && (
            <button className="primario" style={{ marginTop: 14 }} onClick={() => convertir(abierta)}>
              Convertir en venta
            </button>
          )}
        </Modal>
      )}

      {convertida && (
        <Modal
          titulo={`Venta ${convertida.numero} creada`}
          ancho={620}
          onCerrar={() => setConvertida(null)}
        >
          <p style={{ marginTop: 0 }}>
            Total <strong>{dinero(convertida.total)}</strong>. El cliente ya puede escanear su nota.
          </p>
          <NotaQR venta={convertida} />
        </Modal>
      )}
    </>
  );
}

function EditorCotizacion({
  onCerrar,
  onGuardada,
}: {
  onCerrar: () => void;
  onGuardada: () => void;
}) {
  const [lineas, setLineas] = useState<LineaEditable[]>([]);
  const [cliente, setCliente] = useState<Tercero | null>(null);
  const [nombreLibre, setNombreLibre] = useState("");
  const [validez, setValidez] = useState("15");
  const [notas, setNotas] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const { total } = totalesDe(lineas, true);
  const avisos = avisosBajoMinimo(lineas);

  async function guardar(autorizado = false) {
    // Cotizar por debajo del mínimo es prometer venderlo así: se confirma igual
    // que en el punto de venta.
    if (!autorizado && avisos.length) {
      const detalle = avisos.map((a) => `• ${a}`).join("\n");
      if (!confirm(`Estos precios están por debajo del mínimo:\n\n${detalle}\n\n¿Cotizar igual?`)) return;
      autorizado = true;
    }
    setGuardando(true);
    setError("");
    try {
      await apiCotizaciones.crear({
        cliente: cliente?.id ?? null,
        cliente_nombre: cliente ? "" : nombreLibre.trim(),
        validez_dias: Number(validez) || 15,
        notas: notas.trim(),
        autorizar_precio_bajo: autorizado,
        detalles: lineasAPayload(lineas, true),
      });
      onGuardada();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Modal
      titulo="Nueva cotización"
      ancho={820}
      onCerrar={onCerrar}
      pie={
        <>
          <button onClick={onCerrar}>Cancelar</button>
          <button className="primario" disabled={!lineas.length || guardando} onClick={() => guardar()}>
            {guardando ? "Guardando…" : `Guardar · ${dinero(total)}`}
          </button>
        </>
      }
    >
      <Error>{error}</Error>
      <Campo etiqueta="Cliente">
        <SelectorCliente
          cliente={cliente}
          setCliente={setCliente}
          nombreLibre={nombreLibre}
          setNombreLibre={setNombreLibre}
        />
      </Campo>
      <Campo etiqueta="Validez (días)">
        <input value={validez} inputMode="numeric" onChange={(e) => setValidez(e.target.value)} />
      </Campo>
      <EditorLineas lineas={lineas} setLineas={setLineas} fiscal />
      <Campo etiqueta="Notas">
        <textarea value={notas} rows={2} onChange={(e) => setNotas(e.target.value)} />
      </Campo>
    </Modal>
  );
}

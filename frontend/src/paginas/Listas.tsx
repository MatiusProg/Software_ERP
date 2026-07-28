/*
  Listas de pendientes: el mismo objeto que sincroniza la PWA.

  Aquí no hay impuesto (son informales) y cada ítem puede marcarse como
  comprado, igual que se tacha en la PWA.
*/

import { useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiListas, useLista } from "../api/recursos";
import type { Lista, Tercero } from "../api/tipos";
import { useSesion } from "../auth/sesion";
import { SelectorCliente } from "../componentes/SelectorCliente";
import {
  EditorLineas,
  lineasAPayload,
  nuevaLinea,
  totalesDe,
  type LineaEditable,
} from "../componentes/lineas";
import { Campo, Cargando, Error, Modal, Vacio } from "../componentes/ui";
import { dinero, fecha } from "../util/formato";

export function Listas() {
  const { permisos } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const [editando, setEditando] = useState<Lista | "nueva" | null>(null);
  const [error, setError] = useState("");

  const { datos, total, cargando, recargar } = useLista<Lista>("/listas/", {
    search: busqueda || undefined,
  });

  async function borrar(lista: Lista) {
    if (!confirm(`¿Borrar la lista "${lista.titulo}"?`)) return;
    try {
      await apiListas.eliminar(lista.id);
      await recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Listas</h1>
          <p>{total} listas · lo mismo que sincroniza la PWA</p>
        </div>
        <div className="fila">
          <input
            style={{ width: 230 }}
            placeholder="Buscar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          {permisos.puedeVender && (
            <button className="primario" onClick={() => setEditando("nueva")}>
              Nueva lista
            </button>
          )}
        </div>
      </div>

      <Error>{error}</Error>

      <div className="tarjeta tabla-caja">
        {cargando ? (
          <Cargando />
        ) : datos.length === 0 ? (
          <Vacio titulo="Sin listas">Crea una o súbelas desde la PWA.</Vacio>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Título</th>
                <th>Fecha</th>
                <th>Para</th>
                <th>Avance</th>
                <th className="num">Total</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {datos.map((l) => {
                const comprados = l.items.filter((i) => i.comprado).length;
                return (
                  <tr key={l.id} className="clic" onClick={() => setEditando(l)}>
                    <td>
                      <strong>{l.titulo}</strong>
                    </td>
                    <td style={{ color: "var(--tenue)" }}>{fecha(l.creado_en)}</td>
                    <td>{l.cliente_nombre || "—"}</td>
                    <td>
                      <span className="chip">
                        {comprados}/{l.items.length} comprados
                      </span>
                    </td>
                    <td className="num">
                      <strong>{dinero(l.total)}</strong>
                    </td>
                    <td className="num">
                      {permisos.puedeBorrar && (
                        <button
                          className="plano peligro"
                          onClick={(e) => {
                            e.stopPropagation();
                            borrar(l);
                          }}
                        >
                          Borrar
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {editando && (
        <EditorLista
          lista={editando === "nueva" ? null : editando}
          onCerrar={() => setEditando(null)}
          onGuardada={async () => {
            setEditando(null);
            await recargar();
          }}
        />
      )}
    </>
  );
}

function EditorLista({
  lista,
  onCerrar,
  onGuardada,
}: {
  lista: Lista | null;
  onCerrar: () => void;
  onGuardada: () => void;
}) {
  const [titulo, setTitulo] = useState(lista?.titulo ?? "");
  const [cliente, setCliente] = useState<Tercero | null>(null);
  const [nombreLibre, setNombreLibre] = useState(lista?.cliente_nombre ?? "");
  const [lineas, setLineas] = useState<LineaEditable[]>(
    (lista?.items ?? []).map((i) =>
      nuevaLinea({
        producto: i.producto,
        descripcion: i.descripcion,
        detalle: i.detalle,
        modoUnitario: i.cantidad !== null && i.precio_unitario !== null,
        cantidad: i.cantidad ?? "1",
        precioUnitario: i.precio_unitario ?? "",
        total: i.total,
        comprado: !!i.comprado,
      }),
    ),
  );
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const { total } = totalesDe(lineas, false);

  async function guardar() {
    setGuardando(true);
    setError("");
    const cuerpo = {
      titulo: titulo.trim() || "Lista sin título",
      cliente: cliente?.id ?? null,
      cliente_nombre: cliente ? "" : nombreLibre.trim(),
      items: lineasAPayload(
        lineas.map((l) => ({ ...l, comprado: !!l.comprado })),
        false,
      ),
    };
    try {
      if (lista) await apiListas.actualizar(lista.id, cuerpo);
      else await apiListas.crear(cuerpo);
      onGuardada();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Modal
      titulo={lista ? `Lista · ${lista.titulo}` : "Nueva lista"}
      ancho={820}
      onCerrar={onCerrar}
      pie={
        <>
          <button onClick={onCerrar}>Cancelar</button>
          <button className="primario" disabled={guardando} onClick={guardar}>
            {guardando ? "Guardando…" : `Guardar · ${dinero(total)}`}
          </button>
        </>
      }
    >
      <Error>{error}</Error>
      <Campo etiqueta="Título">
        <input
          value={titulo}
          placeholder="VENTA · MAMÁ DE KAREN"
          onChange={(e) => setTitulo(e.target.value)}
        />
      </Campo>
      <Campo etiqueta="Para quién (opcional)">
        <SelectorCliente
          cliente={cliente}
          setCliente={setCliente}
          nombreLibre={nombreLibre}
          setNombreLibre={setNombreLibre}
        />
      </Campo>
      <EditorLineas lineas={lineas} setLineas={setLineas} fiscal={false} conComprado />
    </Modal>
  );
}

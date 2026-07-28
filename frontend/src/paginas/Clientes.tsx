/*
  Terceros: clientes, proveedores y transportadoras.

  Son banderas, no un tipo único: el mismo tercero puede ser cliente y proveedor
  a la vez sin duplicarlo (decisión 6 del PLAN). El WhatsApp que se guarde aquí
  es el que usa el botón "Enviar por WhatsApp" de la nota de venta.
*/

import { useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiTerceros, useLista } from "../api/recursos";
import type { Tercero } from "../api/tipos";
import { useSesion } from "../auth/sesion";
import { Campo, Cargando, Error, Modal, Vacio } from "../componentes/ui";

const VACIO: Partial<Tercero> = {
  nombre: "",
  nit_ci: "",
  es_cliente: true,
  es_proveedor: false,
  es_transportadora: false,
  notas: "",
  activo: true,
  contactos: [],
};

const telefonoDe = (t: Tercero) =>
  t.contactos?.find((c) => c.tipo === "whatsapp" || c.tipo === "telefono")?.valor ?? "";

export function Clientes() {
  const { permisos } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const [rol, setRol] = useState("es_cliente");
  const [editando, setEditando] = useState<Partial<Tercero> | null>(null);

  const { datos, total, cargando, recargar, error } = useLista<Tercero>("/terceros/", {
    search: busqueda || undefined,
    [rol]: rol ? true : undefined,
  });

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Clientes y proveedores</h1>
          <p>{total} registrados</p>
        </div>
        <div className="fila">
          <input
            style={{ width: 220 }}
            placeholder="Buscar…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <select style={{ width: 170 }} value={rol} onChange={(e) => setRol(e.target.value)}>
            <option value="es_cliente">Clientes</option>
            <option value="es_proveedor">Proveedores</option>
            <option value="es_transportadora">Transportadoras</option>
            <option value="">Todos</option>
          </select>
          {permisos.puedeVender && (
            <button className="primario" onClick={() => setEditando({ ...VACIO })}>
              Nuevo
            </button>
          )}
        </div>
      </div>

      <Error>{error}</Error>

      <div className="tarjeta tabla-caja">
        {cargando ? (
          <Cargando />
        ) : datos.length === 0 ? (
          <Vacio titulo="Sin registros">Agrega a quien le vendes o a quien le compras.</Vacio>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>NIT / CI</th>
                <th>Contacto</th>
                <th>Roles</th>
              </tr>
            </thead>
            <tbody>
              {datos.map((t) => (
                <tr key={t.id} className="clic" onClick={() => setEditando(t)}>
                  <td>
                    <strong>{t.nombre}</strong>
                  </td>
                  <td style={{ color: "var(--tenue)" }}>{t.nit_ci || "—"}</td>
                  <td>{telefonoDe(t) || "—"}</td>
                  <td>
                    {t.es_cliente && <span className="chip acento">cliente</span>}{" "}
                    {t.es_proveedor && <span className="chip">proveedor</span>}{" "}
                    {t.es_transportadora && <span className="chip">transporte</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editando && (
        <EditorTercero
          tercero={editando}
          onCerrar={() => setEditando(null)}
          onGuardado={async () => {
            setEditando(null);
            await recargar();
          }}
        />
      )}
    </>
  );
}

function EditorTercero({
  tercero,
  onCerrar,
  onGuardado,
}: {
  tercero: Partial<Tercero>;
  onCerrar: () => void;
  onGuardado: () => void;
}) {
  const [datos, setDatos] = useState<Partial<Tercero>>(tercero);
  const [telefono, setTelefono] = useState(
    tercero.contactos?.find((c) => c.tipo === "whatsapp" || c.tipo === "telefono")?.valor ?? "",
  );
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const cambiar = (cambios: Partial<Tercero>) => setDatos({ ...datos, ...cambios });

  async function guardar() {
    setGuardando(true);
    setError("");
    // Se manda el contacto completo: la API reemplaza la lista de contactos.
    const cuerpo = {
      ...datos,
      contactos: telefono.trim() ? [{ tipo: "whatsapp", valor: telefono.trim() }] : [],
    };
    try {
      if (datos.id) await apiTerceros.actualizar(datos.id, cuerpo);
      else await apiTerceros.crear(cuerpo);
      onGuardado();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Modal
      titulo={datos.id ? `Editar ${datos.nombre}` : "Nuevo registro"}
      onCerrar={onCerrar}
      pie={
        <>
          <button onClick={onCerrar}>Cancelar</button>
          <button className="primario" disabled={guardando} onClick={guardar}>
            {guardando ? "Guardando…" : "Guardar"}
          </button>
        </>
      }
    >
      <Error>{error}</Error>
      <Campo etiqueta="Nombre">
        <input value={datos.nombre ?? ""} onChange={(e) => cambiar({ nombre: e.target.value })} />
      </Campo>
      <div className="fila">
        <div className="crece">
          <Campo etiqueta="NIT / CI">
            <input value={datos.nit_ci ?? ""} onChange={(e) => cambiar({ nit_ci: e.target.value })} />
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="WhatsApp / teléfono">
            <input
              value={telefono}
              placeholder="71234567"
              onChange={(e) => setTelefono(e.target.value)}
            />
          </Campo>
        </div>
      </div>
      <Campo etiqueta="Notas">
        <textarea value={datos.notas ?? ""} rows={2} onChange={(e) => cambiar({ notas: e.target.value })} />
      </Campo>
      <div className="fila">
        {(
          [
            ["es_cliente", "Cliente"],
            ["es_proveedor", "Proveedor"],
            ["es_transportadora", "Transportadora"],
          ] as const
        ).map(([campo, texto]) => (
          <label key={campo} className="fila" style={{ gap: 6 }}>
            <input
              type="checkbox"
              checked={!!datos[campo]}
              onChange={(e) => cambiar({ [campo]: e.target.checked })}
            />
            {texto}
          </label>
        ))}
      </div>
    </Modal>
  );
}

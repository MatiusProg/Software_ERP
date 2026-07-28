/*
  Catálogo: productos y sus precios.

  Los cuatro precios (venta, venta mínimo, compra, compra máximo) son la regla de
  negociación que valida el backend: no se puede vender por debajo del mínimo ni
  comprar por encima del máximo. Aquí solo se capturan; la validación se muestra
  tal como la devuelve la API.
*/

import { useEffect, useState } from "react";

import { mensajeDeError } from "../api/cliente";
import { apiCategorias, apiProductos, useLista } from "../api/recursos";
import type { Categoria, Producto } from "../api/tipos";
import { useSesion } from "../auth/sesion";
import { Campo, Cargando, Error, Modal, Vacio } from "../componentes/ui";
import { cantidad, dinero } from "../util/formato";

const VACIO: Partial<Producto> = {
  sku: "",
  codigo_barras: "",
  nombre: "",
  categoria: null,
  unidad: "unidad",
  es_servicio: false,
  precio_venta: "0",
  precio_venta_minimo: "0",
  precio_compra: "0",
  precio_compra_maximo: "0",
  stock: "0",
  impuesto: "13",
  activo: true,
};

export function Productos() {
  const { permisos } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const [categoria, setCategoria] = useState("");
  const [editando, setEditando] = useState<Partial<Producto> | null>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [error, setError] = useState("");

  const { datos, total, cargando, recargar } = useLista<Producto>("/productos/", {
    search: busqueda || undefined,
    categoria: categoria || undefined,
  });

  useEffect(() => {
    apiCategorias.listar().then((p) => setCategorias(p.results)).catch(() => setCategorias([]));
  }, []);

  async function borrar(p: Producto) {
    if (!confirm(`¿Borrar "${p.nombre}"?`)) return;
    try {
      await apiProductos.eliminar(p.id);
      await recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  return (
    <>
      <div className="encabezado">
        <div>
          <h1>Productos</h1>
          <p>{total} en el catálogo</p>
        </div>
        <div className="fila">
          <input
            style={{ width: 240 }}
            placeholder="Buscar por nombre, SKU o código…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <select style={{ width: 180 }} value={categoria} onChange={(e) => setCategoria(e.target.value)}>
            <option value="">Todas las categorías</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </select>
          {permisos.puedeEditarCatalogo && (
            <button className="primario" onClick={() => setEditando({ ...VACIO })}>
              Nuevo producto
            </button>
          )}
        </div>
      </div>

      <Error>{error}</Error>

      <div className="tarjeta tabla-caja">
        {cargando ? (
          <Cargando />
        ) : datos.length === 0 ? (
          <Vacio titulo="Sin productos">Agrega el primero para poder venderlo.</Vacio>
        ) : (
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Nombre</th>
                <th>Categoría</th>
                <th className="num">Precio</th>
                <th className="num">Mínimo</th>
                <th className="num">Stock</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {datos.map((p) => (
                <tr
                  key={p.id}
                  className={permisos.puedeEditarCatalogo ? "clic" : ""}
                  onClick={() => permisos.puedeEditarCatalogo && setEditando(p)}
                >
                  <td style={{ fontFamily: "ui-monospace, monospace", fontSize: 13 }}>{p.sku}</td>
                  <td>
                    <strong>{p.nombre}</strong>
                    {!p.activo && <span className="chip mal" style={{ marginLeft: 6 }}>inactivo</span>}
                    {p.es_servicio && <span className="chip" style={{ marginLeft: 6 }}>servicio</span>}
                  </td>
                  <td style={{ color: "var(--tenue)" }}>{p.categoria_nombre ?? "—"}</td>
                  <td className="num">
                    <strong>{dinero(p.precio_venta)}</strong>
                  </td>
                  <td className="num" style={{ color: "var(--tenue)" }}>{dinero(p.precio_venta_minimo)}</td>
                  <td className="num">{p.es_servicio ? "—" : cantidad(p.stock)}</td>
                  <td className="num">
                    {permisos.puedeBorrar && (
                      <button
                        className="plano peligro"
                        onClick={(e) => {
                          e.stopPropagation();
                          borrar(p);
                        }}
                      >
                        Borrar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editando && (
        <EditorProducto
          producto={editando}
          categorias={categorias}
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

function EditorProducto({
  producto,
  categorias,
  onCerrar,
  onGuardado,
}: {
  producto: Partial<Producto>;
  categorias: Categoria[];
  onCerrar: () => void;
  onGuardado: () => void;
}) {
  const [datos, setDatos] = useState<Partial<Producto>>(producto);
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const cambiar = (cambios: Partial<Producto>) => setDatos({ ...datos, ...cambios });

  async function guardar() {
    setGuardando(true);
    setError("");
    const cuerpo = { ...datos, categoria: datos.categoria || null };
    try {
      if (datos.id) await apiProductos.actualizar(datos.id, cuerpo);
      else await apiProductos.crear(cuerpo);
      onGuardado();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <Modal
      titulo={datos.id ? `Editar ${datos.nombre}` : "Nuevo producto"}
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
          <Campo etiqueta="SKU">
            <input value={datos.sku ?? ""} onChange={(e) => cambiar({ sku: e.target.value })} />
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="Código de barras">
            <input
              value={datos.codigo_barras ?? ""}
              onChange={(e) => cambiar({ codigo_barras: e.target.value })}
            />
          </Campo>
        </div>
      </div>
      <div className="fila">
        <div className="crece">
          <Campo etiqueta="Categoría">
            <select
              value={datos.categoria ?? ""}
              onChange={(e) => cambiar({ categoria: e.target.value ? Number(e.target.value) : null })}
            >
              <option value="">Sin categoría</option>
              {categorias.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="Unidad">
            <input value={datos.unidad ?? ""} onChange={(e) => cambiar({ unidad: e.target.value })} />
          </Campo>
        </div>
      </div>

      <div className="fila">
        <div className="crece">
          <Campo etiqueta="Precio de venta">
            <input
              inputMode="decimal"
              value={datos.precio_venta ?? ""}
              onChange={(e) => cambiar({ precio_venta: e.target.value })}
            />
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="Venta mínima">
            <input
              inputMode="decimal"
              value={datos.precio_venta_minimo ?? ""}
              onChange={(e) => cambiar({ precio_venta_minimo: e.target.value })}
            />
          </Campo>
        </div>
      </div>
      <div className="fila">
        <div className="crece">
          <Campo etiqueta="Precio de compra">
            <input
              inputMode="decimal"
              value={datos.precio_compra ?? ""}
              onChange={(e) => cambiar({ precio_compra: e.target.value })}
            />
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="Compra máxima">
            <input
              inputMode="decimal"
              value={datos.precio_compra_maximo ?? ""}
              onChange={(e) => cambiar({ precio_compra_maximo: e.target.value })}
            />
          </Campo>
        </div>
      </div>
      <div className="fila">
        <div className="crece">
          <Campo etiqueta="Stock">
            <input
              inputMode="decimal"
              value={datos.stock ?? ""}
              disabled={datos.es_servicio}
              onChange={(e) => cambiar({ stock: e.target.value })}
            />
          </Campo>
        </div>
        <div className="crece">
          <Campo etiqueta="Impuesto (%)">
            <input
              inputMode="decimal"
              value={datos.impuesto ?? ""}
              onChange={(e) => cambiar({ impuesto: e.target.value })}
            />
          </Campo>
        </div>
      </div>

      <div className="fila">
        <label className="fila" style={{ gap: 6 }}>
          <input
            type="checkbox"
            checked={!!datos.es_servicio}
            onChange={(e) => cambiar({ es_servicio: e.target.checked })}
          />
          Es un servicio (sin stock)
        </label>
        <label className="fila" style={{ gap: 6 }}>
          <input
            type="checkbox"
            checked={datos.activo ?? true}
            onChange={(e) => cambiar({ activo: e.target.checked })}
          />
          Activo
        </label>
      </div>
    </Modal>
  );
}

/*
  Marco del panel.

  Escritorio (≥ 960 px): barra lateral con el logo, el negocio, la navegación,
  el modo de color y el usuario.
  Celular: cabecera arriba (negocio + usuario) y cinco pestañas abajo, al
  alcance del pulgar. Lo que no entra en las pestañas va en la hoja «Más».

  Las sucursales llegan con la Fase 4 (inventario); hasta entonces el bloque del
  negocio muestra solo la organización activa.
*/

import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useSesion } from "../auth/sesion";
import {
  IconoClientes,
  IconoCotizaciones,
  IconoListas,
  IconoMas,
  IconoProductos,
  IconoSalir,
  IconoVender,
  IconoVentas,
} from "./Iconos";
import { Logo, SelectorTema } from "./Tema";
import { Modal } from "./ui";

const SECCIONES = [
  { a: "/venta", texto: "Vender", Icono: IconoVender, enPestanas: true },
  { a: "/ventas", texto: "Ventas", Icono: IconoVentas, enPestanas: true },
  { a: "/productos", texto: "Productos", Icono: IconoProductos, enPestanas: true },
  { a: "/clientes", texto: "Clientes", Icono: IconoClientes, enPestanas: true },
  { a: "/cotizaciones", texto: "Cotizaciones", Icono: IconoCotizaciones, enPestanas: false },
  { a: "/listas", texto: "Listas", Icono: IconoListas, enPestanas: false },
];

const claseActiva = ({ isActive }: { isActive: boolean }) => (isActive ? "activo" : "");

export function Layout() {
  const { usuario, organizacion, salir } = useSesion();
  const { pathname } = useLocation();
  const [verMas, setVerMas] = useState(false);

  const nombre = usuario?.nombre_completo || usuario?.email || "";
  const iniciales = nombre
    .split(/[\s@.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
  const masActivo = SECCIONES.some((s) => !s.enPestanas && pathname.startsWith(s.a));

  const tarjetaUsuario = (
    <div className="usuario">
      <span className="avatar" aria-hidden="true">{iniciales || "?"}</span>
      <div className="datos">
        <div title={usuario?.email}>{nombre}</div>
        <small>{usuario?.rol_activo}</small>
      </div>
    </div>
  );

  return (
    <div className="app">
      <aside className="lateral">
        <div className="logo"><Logo alto={30} /></div>
        <div className="negocio">
          <small>Negocio</small>
          <strong>{organizacion || "—"}</strong>
        </div>
        <nav aria-label="Secciones">
          {SECCIONES.map(({ a, texto, Icono }) => (
            <NavLink key={a} to={a} className={claseActiva}>
              <Icono />
              {texto}
            </NavLink>
          ))}
        </nav>
        <div className="pie-lateral">
          <SelectorTema />
          <div className="fila" style={{ flexWrap: "nowrap" }}>
            {tarjetaUsuario}
            <button className="plano icono" onClick={salir} title="Cerrar sesión" aria-label="Cerrar sesión">
              <IconoSalir />
            </button>
          </div>
        </div>
      </aside>

      <div className="principal">
        <header className="cabecera-movil">
          <div className="negocio-movil">
            <small>Negocio</small>
            <strong>{organizacion || "Kinemart"}</strong>
          </div>
          <Logo soloK alto={30} />
        </header>

        <main className="contenido">
          <Outlet />
        </main>
      </div>

      <nav className="nav-inferior" aria-label="Secciones">
        {SECCIONES.filter((s) => s.enPestanas).map(({ a, texto, Icono }) => (
          <NavLink key={a} to={a} className={claseActiva}>
            <Icono />
            {texto}
          </NavLink>
        ))}
        <button type="button" className={masActivo ? "activo" : ""} onClick={() => setVerMas(true)}>
          <IconoMas />
          Más
        </button>
      </nav>

      {verMas && (
        <Modal titulo="Más" onCerrar={() => setVerMas(false)}>
          <div className="hoja-mas">
            {SECCIONES.filter((s) => !s.enPestanas).map(({ a, texto, Icono }) => (
              <NavLink key={a} to={a} onClick={() => setVerMas(false)}>
                <Icono />
                {texto}
              </NavLink>
            ))}
            <div style={{ margin: "10px 0 2px", fontSize: 13, color: "var(--tenue)", fontWeight: 600 }}>
              Modo de color
            </div>
            <SelectorTema />
            <div className="fila-hoja" style={{ marginTop: 10 }}>
              {tarjetaUsuario}
            </div>
            <button className="peligro" onClick={salir}>
              <IconoSalir />
              Cerrar sesión
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

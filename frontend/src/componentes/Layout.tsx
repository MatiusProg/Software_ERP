/* Marco del panel: barra de navegación + contenido de la ruta activa. */

import { NavLink, Outlet } from "react-router-dom";

import { useSesion } from "../auth/sesion";
import { InterruptorTema } from "./Tema";

const SECCIONES = [
  { a: "/venta", texto: "Punto de venta" },
  { a: "/ventas", texto: "Ventas" },
  { a: "/cotizaciones", texto: "Cotizaciones" },
  { a: "/listas", texto: "Listas" },
  { a: "/productos", texto: "Productos" },
  { a: "/clientes", texto: "Clientes" },
];

export function Layout() {
  const { usuario, organizacion, salir } = useSesion();
  const iniciales = (usuario?.nombre_completo || usuario?.email || "?")
    .split(/[\s@.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");

  return (
    <div className="app">
      <header className="barra">
        <div className="marca">
          <span className="punto" />
          {organizacion || "ERP"}
        </div>
        <nav>
          {SECCIONES.map((s) => (
            <NavLink key={s.a} to={s.a} className={({ isActive }) => (isActive ? "activo" : "")}>
              {s.texto}
            </NavLink>
          ))}
        </nav>
        <div className="derecha">
          <InterruptorTema />
          <span className="chip acento" title={usuario?.email}>
            {iniciales} · {usuario?.rol_activo}
          </span>
          <button className="plano" onClick={salir}>
            Salir
          </button>
        </div>
      </header>
      <main className="contenido ancho">
        <Outlet />
      </main>
    </div>
  );
}

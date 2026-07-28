/*
  Rutas del panel.

  Todo cuelga de <ProveedorSesion>: mientras se reanuda la sesión se muestra un
  cargando, sin sesión se muestra el login, y con sesión el Layout con las
  pantallas dentro.
*/

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProveedorSesion, useSesion } from "./auth/sesion";
import { Layout } from "./componentes/Layout";
import { Cargando } from "./componentes/ui";
import { Clientes } from "./paginas/Clientes";
import { Cotizaciones } from "./paginas/Cotizaciones";
import { Listas } from "./paginas/Listas";
import { Login } from "./paginas/Login";
import { Productos } from "./paginas/Productos";
import { PuntoDeVenta } from "./paginas/PuntoDeVenta";
import { Ventas } from "./paginas/Ventas";

function Rutas() {
  const { usuario, cargando } = useSesion();

  if (cargando) return <Cargando texto="Abriendo tu sesión…" />;
  if (!usuario) return <Login />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/venta" element={<PuntoDeVenta />} />
        <Route path="/ventas" element={<Ventas />} />
        <Route path="/cotizaciones" element={<Cotizaciones />} />
        <Route path="/listas" element={<Listas />} />
        <Route path="/productos" element={<Productos />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="*" element={<Navigate to="/venta" replace />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <ProveedorSesion>
        <Rutas />
      </ProveedorSesion>
    </BrowserRouter>
  );
}

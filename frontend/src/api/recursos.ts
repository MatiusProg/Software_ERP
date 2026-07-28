/*
  Acceso a los recursos de la API y ganchos de datos.

  Se usa axios + un gancho `useLista` propio en vez de una librería de estado de
  servidor: el panel tiene pocas pantallas y así no se añade una dependencia (ni
  una capa de conceptos) para resolver "traer, recargar y mostrar el error".
*/

import { useCallback, useEffect, useState } from "react";

import { api, mensajeDeError } from "./cliente";
import type { Categoria, Cotizacion, Lista, Pagina, Producto, Tercero, Venta } from "./tipos";

export type Parametros = Record<string, string | number | boolean | undefined>;

export async function listar<T>(ruta: string, params?: Parametros): Promise<Pagina<T>> {
  const { data } = await api.get<Pagina<T>>(ruta, { params });
  return data;
}

export const crear = <T,>(ruta: string, cuerpo: unknown) =>
  api.post<T>(ruta, cuerpo).then((r) => r.data);

export const actualizar = <T,>(ruta: string, id: number, cuerpo: unknown) =>
  api.patch<T>(`${ruta}${id}/`, cuerpo).then((r) => r.data);

export const eliminar = (ruta: string, id: number) => api.delete(`${ruta}${id}/`);

/** Trae una página de un recurso y la recarga cuando cambian los parámetros. */
export function useLista<T>(ruta: string, params?: Parametros) {
  const [datos, setDatos] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  // Las dependencias se comparan por valor: así un objeto nuevo con los mismos
  // filtros no dispara una recarga infinita.
  const clave = JSON.stringify(params ?? {});

  const recargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      const pagina = await listar<T>(ruta, JSON.parse(clave));
      setDatos(pagina.results);
      setTotal(pagina.count);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, [ruta, clave]);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  return { datos, total, cargando, error, recargar, setError };
}

// Rutas (el router de DRF exige la barra final).
export const RUTAS = {
  productos: "/productos/",
  categorias: "/categorias/",
  terceros: "/terceros/",
  ventas: "/ventas/",
  cotizaciones: "/cotizaciones/",
  listas: "/listas/",
} as const;

export const apiProductos = {
  listar: (p?: Parametros) => listar<Producto>(RUTAS.productos, p),
  crear: (c: Partial<Producto>) => crear<Producto>(RUTAS.productos, c),
  actualizar: (id: number, c: Partial<Producto>) => actualizar<Producto>(RUTAS.productos, id, c),
  eliminar: (id: number) => eliminar(RUTAS.productos, id),
};

export const apiCategorias = {
  listar: (p?: Parametros) => listar<Categoria>(RUTAS.categorias, p),
  crear: (c: Partial<Categoria>) => crear<Categoria>(RUTAS.categorias, c),
};

export const apiTerceros = {
  listar: (p?: Parametros) => listar<Tercero>(RUTAS.terceros, p),
  crear: (c: Partial<Tercero>) => crear<Tercero>(RUTAS.terceros, c),
  actualizar: (id: number, c: Partial<Tercero>) => actualizar<Tercero>(RUTAS.terceros, id, c),
};

export const apiVentas = {
  listar: (p?: Parametros) => listar<Venta>(RUTAS.ventas, p),
  crear: (c: unknown) => crear<Venta>(RUTAS.ventas, c),
  actualizar: (id: number, c: unknown) => actualizar<Venta>(RUTAS.ventas, id, c),
  obtener: (id: number) => api.get<Venta>(`${RUTAS.ventas}${id}/`).then((r) => r.data),
};

export const apiCotizaciones = {
  listar: (p?: Parametros) => listar<Cotizacion>(RUTAS.cotizaciones, p),
  crear: (c: unknown) => crear<Cotizacion>(RUTAS.cotizaciones, c),
  convertirEnVenta: (id: number) =>
    api.post<Venta>(`${RUTAS.cotizaciones}${id}/convertir_en_venta/`).then((r) => r.data),
};

export const apiListas = {
  listar: (p?: Parametros) => listar<Lista>(RUTAS.listas, p),
  crear: (c: unknown) => crear<Lista>(RUTAS.listas, c),
  actualizar: (id: number, c: unknown) => actualizar<Lista>(RUTAS.listas, id, c),
  eliminar: (id: number) => eliminar(RUTAS.listas, id),
};

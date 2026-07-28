/*
  Sesión del panel: quién está dentro, en qué organización y con qué rol.

  Al arrancar, si hay un `refresh` guardado se pide un `access` nuevo y se carga
  `/api/yo/`; así el usuario no vuelve a escribir la contraseña en cada recarga.
  Los permisos se calculan aquí una sola vez para que las pantallas solo
  pregunten `permisos.puedeVender`, sin repetir la tabla de roles.
*/

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import axios from "axios";

import {
  URL_API,
  alExpirarSesion,
  api,
  guardarTokens,
  limpiarTokens,
  sesionGuardada,
} from "../api/cliente";
import type { Rol, Yo } from "../api/tipos";

interface Permisos {
  /** Crear/editar ventas, cotizaciones, listas y clientes. */
  puedeVender: boolean;
  /** Crear/editar productos y categorías. */
  puedeEditarCatalogo: boolean;
  /** Borrar documentos y productos. */
  puedeBorrar: boolean;
}

interface Contexto {
  usuario: Yo | null;
  cargando: boolean;
  permisos: Permisos;
  organizacion: string;
  entrar: (email: string, password: string) => Promise<void>;
  salir: () => void;
}

const SesionCtx = createContext<Contexto | null>(null);

function permisosDe(rol: Rol | null): Permisos {
  const admin = rol === "propietario" || rol === "admin";
  return {
    puedeVender: admin || rol === "vendedor",
    puedeEditarCatalogo: admin,
    puedeBorrar: admin,
  };
}

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Yo | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargarPerfil = useCallback(async () => {
    const { data } = await api.get<Yo>("/yo/");
    setUsuario(data);
  }, []);

  const salir = useCallback(() => {
    limpiarTokens();
    setUsuario(null);
  }, []);

  // Reanudar sesión al abrir la pestaña.
  useEffect(() => {
    alExpirarSesion(salir);
    (async () => {
      if (!sesionGuardada()) {
        setCargando(false);
        return;
      }
      try {
        const { data } = await axios.post(`${URL_API}/api/auth/token/refresh/`, {
          refresh: sesionGuardada(),
        });
        guardarTokens(data.access, data.refresh);
        await cargarPerfil();
      } catch {
        limpiarTokens();
      } finally {
        setCargando(false);
      }
    })();
  }, [cargarPerfil, salir]);

  const entrar = useCallback(
    async (email: string, password: string) => {
      const { data } = await axios.post(`${URL_API}/api/auth/token/`, { email, password });
      guardarTokens(data.access, data.refresh);
      await cargarPerfil();
    },
    [cargarPerfil],
  );

  const valor = useMemo<Contexto>(() => {
    const activa = usuario?.membresias.find(
      (m) => m.organizacion.id === usuario?.organizacion_activa,
    );
    return {
      usuario,
      cargando,
      permisos: permisosDe(usuario?.rol_activo ?? null),
      organizacion: activa?.organizacion.nombre ?? "",
      entrar,
      salir,
    };
  }, [usuario, cargando, entrar, salir]);

  return <SesionCtx.Provider value={valor}>{children}</SesionCtx.Provider>;
}

export function useSesion() {
  const ctx = useContext(SesionCtx);
  if (!ctx) throw new Error("useSesion debe usarse dentro de <ProveedorSesion>");
  return ctx;
}

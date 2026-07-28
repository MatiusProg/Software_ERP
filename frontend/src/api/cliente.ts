/*
  Cliente HTTP contra la API del ERP.

  Manejo de tokens (decisión de Fase 3):
  - `access` vive **solo en memoria**: si se cierra la pestaña se pierde, que es
    lo que queremos (un token robado del localStorage sirve una hora).
  - `refresh` vive en localStorage para poder reanudar la sesión al recargar.
  - Un interceptor reintenta **una sola vez** ante un 401: pide un access nuevo
    con el refresh y repite la petición original. Como el backend rota los
    refresh (`ROTATE_REFRESH_TOKENS`), se guarda también el nuevo.
*/

import axios, { AxiosError, type AxiosRequestConfig } from "axios";

export const URL_API = (
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const CLAVE_REFRESH = "erp-refresh";

let tokenAcceso: string | null = null;
let alCerrarSesion: (() => void) | null = null;

export const sesionGuardada = () => localStorage.getItem(CLAVE_REFRESH);

export function guardarTokens(access: string, refresh?: string) {
  tokenAcceso = access;
  if (refresh) localStorage.setItem(CLAVE_REFRESH, refresh);
}

export function limpiarTokens() {
  tokenAcceso = null;
  localStorage.removeItem(CLAVE_REFRESH);
}

/** La sesión de React registra aquí qué hacer cuando el refresh ya no sirve. */
export function alExpirarSesion(fn: () => void) {
  alCerrarSesion = fn;
}

export const api = axios.create({ baseURL: `${URL_API}/api`, timeout: 20000 });

api.interceptors.request.use((config) => {
  if (tokenAcceso) config.headers.Authorization = `Bearer ${tokenAcceso}`;
  return config;
});

/** Pide un access nuevo con el refresh guardado. Devuelve null si ya no vale. */
export async function refrescarAcceso(): Promise<string | null> {
  const refresh = localStorage.getItem(CLAVE_REFRESH);
  if (!refresh) return null;
  try {
    const { data } = await axios.post(`${URL_API}/api/auth/token/refresh/`, { refresh });
    guardarTokens(data.access, data.refresh);
    return data.access;
  } catch {
    limpiarTokens();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _reintentado?: boolean };
    const esLogin = original?.url?.includes("/auth/token");
    if (error.response?.status === 401 && original && !original._reintentado && !esLogin) {
      original._reintentado = true;
      const nuevo = await refrescarAcceso();
      if (nuevo) return api(original);
      alCerrarSesion?.();
    }
    return Promise.reject(error);
  },
);

/**
 * Convierte el error de DRF en un texto legible.
 * DRF responde `{"campo": ["mensaje"], "detail": "..."}`; sin esto el usuario
 * vería "[object Object]".
 */
export function mensajeDeError(error: unknown): string {
  const err = error as AxiosError<Record<string, unknown>>;
  if (!err?.isAxiosError) return String(error);
  if (!err.response) return "No se pudo conectar con el servidor. ¿Está encendido?";
  const data = err.response.data;
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    const partes: string[] = [];
    for (const [campo, valor] of Object.entries(data)) {
      const texto = Array.isArray(valor) ? valor.join(" ") : String(valor);
      partes.push(campo === "detail" || campo === "non_field_errors" ? texto : `${campo}: ${texto}`);
    }
    if (partes.length) return partes.join("\n");
  }
  return `Error ${err.response.status}`;
}

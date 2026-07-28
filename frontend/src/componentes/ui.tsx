/* Piezas de interfaz compartidas. Todas leen las variables CSS del tema. */

import { useEffect, type ReactNode } from "react";

export function Campo({
  etiqueta,
  children,
}: {
  etiqueta: string;
  children: ReactNode;
}) {
  return (
    <label className="campo">
      <span>{etiqueta}</span>
      {children}
    </label>
  );
}

export function Error({ children }: { children?: ReactNode }) {
  if (!children) return null;
  return <div className="error">{children}</div>;
}

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return <div className="cargando">{texto}</div>;
}

export function Vacio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="vacio">
      <h3>{titulo}</h3>
      {children}
    </div>
  );
}

/** Modal accesible: cierra con Escape y con clic fuera. */
export function Modal({
  titulo,
  onCerrar,
  children,
  pie,
  ancho,
}: {
  titulo: string;
  onCerrar: () => void;
  children: ReactNode;
  pie?: ReactNode;
  ancho?: number;
}) {
  useEffect(() => {
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCerrar();
    };
    document.addEventListener("keydown", alTeclear);
    return () => document.removeEventListener("keydown", alTeclear);
  }, [onCerrar]);

  return (
    <div className="velo" onMouseDown={(e) => e.target === e.currentTarget && onCerrar()}>
      <div className="modal" style={ancho ? { maxWidth: ancho } : undefined} role="dialog" aria-modal>
        <div className="cabecera">
          <h2>{titulo}</h2>
          <button className="plano icono" onClick={onCerrar} aria-label="Cerrar">
            ✕
          </button>
        </div>
        <div className="cuerpo">{children}</div>
        {pie && <div className="pie">{pie}</div>}
      </div>
    </div>
  );
}

/** Chip de estado con color según el valor (pagado/anulada/pendiente…). */
export function ChipEstado({ estado, texto }: { estado: string; texto?: string }) {
  const clase =
    estado === "pagado" || estado === "aceptada" || estado === "confirmada"
      ? "ok"
      : estado === "anulada" || estado === "rechazada"
        ? "mal"
        : estado === "pendiente" || estado === "parcial" || estado === "enviada"
          ? "espera"
          : "";
  return <span className={`chip ${clase}`}>{texto ?? estado}</span>;
}

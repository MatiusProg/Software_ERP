/* Íconos de trazo del panel. Toman el color del texto (currentColor). */

import type { ReactNode } from "react";

function Trazo({ children, tam = 20 }: { children: ReactNode; tam?: number }) {
  return (
    <svg width={tam} height={tam} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {children}
    </svg>
  );
}

export const IconoVender = () => (
  <Trazo><circle cx="9" cy="20" r="1.5" /><circle cx="18" cy="20" r="1.5" /><path d="M2 3h3l2.6 12.4a1 1 0 0 0 1 .8h9.7a1 1 0 0 0 1-.8L21 7H6" /></Trazo>
);
export const IconoVentas = () => (
  <Trazo><path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2z" /><path d="M9 8h6M9 12h6" /></Trazo>
);
export const IconoCotizaciones = () => (
  <Trazo><path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></Trazo>
);
export const IconoProductos = () => (
  <Trazo><path d="m21 8-9-5-9 5 9 5z" /><path d="M3 8v8l9 5 9-5V8M12 13v8" /></Trazo>
);
export const IconoClientes = () => (
  <Trazo><circle cx="9" cy="8" r="4" /><path d="M2 21a7 7 0 0 1 14 0M17 4a4 4 0 0 1 0 8M22 21a7 7 0 0 0-4-6.3" /></Trazo>
);
export const IconoListas = () => (
  <Trazo><path d="M9 6h12M9 12h12M9 18h12M4 6h.01M4 12h.01M4 18h.01" /></Trazo>
);
export const IconoMas = () => <Trazo><path d="M4 6h16M4 12h16M4 18h16" /></Trazo>;
export const IconoSalir = () => (
  <Trazo><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l-5-5 5-5M5 12h11" /></Trazo>
);
export const IconoOjo = ({ tachado = false }: { tachado?: boolean }) => (
  <Trazo>
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" />
    <circle cx="12" cy="12" r="3" />
    {tachado && <path d="M3 3l18 18" />}
  </Trazo>
);

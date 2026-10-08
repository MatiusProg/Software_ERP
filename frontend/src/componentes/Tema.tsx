/*
  Modo de color: noche (por defecto), claro y tecno.

  El modo se aplica en `index.html` antes de pintar (para que no haya destello);
  aquí solo se cambia `data-tema` en <html>, se guarda la elección y se ajusta el
  color de la barra del navegador en el celular. Ningún componente conoce los
  colores: todos leen las variables de estilos.css.
*/

import { useEffect, useState } from "react";

export type Tema = "noche" | "claro" | "tecno";

const COLOR_BARRA: Record<Tema, string> = {
  noche: "#16241D",
  claro: "#F4F7F5",
  tecno: "#0E1318",
};

const temaActual = (): Tema => {
  const t = document.documentElement.dataset.tema;
  return t === "claro" || t === "tecno" ? t : "noche";
};

function aplicar(tema: Tema) {
  document.documentElement.dataset.tema = tema;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", COLOR_BARRA[tema]);
  try {
    localStorage.setItem("kinemart-tema", tema);
  } catch {
    // Navegación privada sin almacenamiento: el modo dura lo que dure la pestaña.
  }
}

/** Modo actual; se actualiza cuando cualquier selector lo cambia. */
export function useTema(): Tema {
  const [tema, setTema] = useState<Tema>(temaActual);
  useEffect(() => {
    const obs = new MutationObserver(() => setTema(temaActual()));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-tema"] });
    return () => obs.disconnect();
  }, []);
  return tema;
}

const OPCIONES: { tema: Tema; nombre: string; icono: React.ReactNode }[] = [
  {
    tema: "noche",
    nombre: "Noche",
    icono: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
  },
  {
    tema: "claro",
    nombre: "Claro",
    icono: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </>
    ),
  },
  {
    tema: "tecno",
    nombre: "Tecno",
    icono: (
      <>
        <rect x="6" y="6" width="12" height="12" rx="1.5" />
        <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" />
      </>
    ),
  },
];

/** Selector de los tres modos. `compacto` muestra solo los íconos. */
export function SelectorTema({ compacto = false }: { compacto?: boolean }) {
  const tema = useTema();
  return (
    <div className={`selector-tema${compacto ? " compacto" : ""}`} role="radiogroup" aria-label="Modo de color">
      {OPCIONES.map((o) => (
        <button
          key={o.tema}
          type="button"
          role="radio"
          aria-checked={tema === o.tema}
          className={tema === o.tema ? "activo" : ""}
          title={`Modo ${o.nombre.toLowerCase()}`}
          onClick={() => aplicar(o.tema)}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            {o.icono}
          </svg>
          {!compacto && <span>{o.nombre}</span>}
        </button>
      ))}
    </div>
  );
}

/** Logo según el modo: el de palabra oscura solo se ve bien sobre fondo claro. */
export function Logo({ alto = 28, soloK = false }: { alto?: number; soloK?: boolean }) {
  const tema = useTema();
  if (soloK) {
    const k = tema === "claro" ? "kinemart-k.svg" : "kinemart-k-claro.svg";
    return <img src={`/marca/${k}`} alt="Kinemart" style={{ height: alto }} />;
  }
  const archivo = tema === "claro" ? "kinemart-logo.svg" : "kinemart-logo-blanco.svg";
  return <img src={`/marca/${archivo}`} alt="Kinemart" style={{ height: alto, width: "auto" }} />;
}

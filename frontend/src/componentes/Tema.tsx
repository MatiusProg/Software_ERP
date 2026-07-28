/*
  Interruptor claro/oscuro.

  El tema se aplica en `index.html` antes de pintar (para que no haya destello);
  aquí solo se cambia el atributo `data-tema` de <html> y se guarda la elección.
*/

import { useState } from "react";

type Tema = "claro" | "oscuro";

const temaActual = (): Tema =>
  (document.documentElement.dataset.tema as Tema) ?? "claro";

export function InterruptorTema() {
  const [tema, setTema] = useState<Tema>(temaActual);

  function alternar() {
    const nuevo: Tema = tema === "oscuro" ? "claro" : "oscuro";
    document.documentElement.dataset.tema = nuevo;
    localStorage.setItem("erp-tema", nuevo);
    setTema(nuevo);
  }

  return (
    <button
      className="plano icono"
      onClick={alternar}
      title={tema === "oscuro" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      aria-label="Cambiar tema"
    >
      {tema === "oscuro" ? "☀️" : "🌙"}
    </button>
  );
}

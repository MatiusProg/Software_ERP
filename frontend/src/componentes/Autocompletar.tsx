/*
  Buscador con sugerencias, genérico (productos, clientes…).

  Detalles pensados para el mostrador:
  - la búsqueda se retrasa 220 ms para no disparar una petición por tecla;
  - Enter elige la primera sugerencia (vender sin soltar el teclado);
  - Escape cierra la lista.
*/

import { useEffect, useRef, useState, type ReactNode } from "react";

interface Props<T> {
  placeholder: string;
  buscar: (texto: string) => Promise<T[]>;
  pintar: (item: T) => ReactNode;
  alElegir: (item: T) => void;
  /** Texto libre confirmado con Enter cuando no hay sugerencia elegida. */
  alTextoLibre?: (texto: string) => void;
  autoFocus?: boolean;
  refExterna?: React.RefObject<HTMLInputElement | null>;
}

export function Autocompletar<T>({
  placeholder,
  buscar,
  pintar,
  alElegir,
  alTextoLibre,
  autoFocus,
  refExterna,
}: Props<T>) {
  const [texto, setTexto] = useState("");
  const [items, setItems] = useState<T[]>([]);
  const [abierto, setAbierto] = useState(false);
  const propio = useRef<HTMLInputElement>(null);
  const entrada = refExterna ?? propio;

  useEffect(() => {
    if (!texto.trim()) {
      setItems([]);
      return;
    }
    let vigente = true;
    const t = setTimeout(async () => {
      try {
        const resultado = await buscar(texto.trim());
        if (vigente) {
          setItems(resultado);
          setAbierto(true);
        }
      } catch {
        if (vigente) setItems([]);
      }
    }, 220);
    return () => {
      vigente = false;
      clearTimeout(t);
    };
    // `buscar` se recrea en cada render de la página; depender solo del texto
    // evita un bucle de peticiones.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texto]);

  function elegir(item: T) {
    alElegir(item);
    setTexto("");
    setItems([]);
    setAbierto(false);
    entrada.current?.focus();
  }

  return (
    <div className="buscador">
      <input
        ref={entrada}
        value={texto}
        autoFocus={autoFocus}
        placeholder={placeholder}
        onChange={(e) => setTexto(e.target.value)}
        onFocus={() => items.length && setAbierto(true)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setAbierto(false);
          if (e.key === "Enter") {
            e.preventDefault();
            if (abierto && items.length) elegir(items[0]);
            else if (alTextoLibre && texto.trim()) {
              alTextoLibre(texto.trim());
              setTexto("");
            }
          }
        }}
      />
      {abierto && items.length > 0 && (
        <div className="sugerencias">
          {items.map((item, i) => (
            <button key={i} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => elegir(item)}>
              {pintar(item)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

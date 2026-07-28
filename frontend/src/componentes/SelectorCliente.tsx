/*
  Elegir el cliente de un documento.

  Dos caminos, a propósito: el cliente **registrado** (FK a Tercero, sirve para
  historial y WhatsApp) o el **nombre libre** para la venta de mostrador, que es
  la mayoría. Nunca obliga a registrar a nadie para poder cobrar.
*/

import { useState } from "react";

import { apiTerceros } from "../api/recursos";
import { mensajeDeError } from "../api/cliente";
import type { Tercero } from "../api/tipos";
import { Autocompletar } from "./Autocompletar";

interface Props {
  cliente: Tercero | null;
  setCliente: (t: Tercero | null) => void;
  nombreLibre: string;
  setNombreLibre: (n: string) => void;
}

export function SelectorCliente({ cliente, setCliente, nombreLibre, setNombreLibre }: Props) {
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);

  if (cliente) {
    return (
      <div className="fila">
        <span className="chip acento">{cliente.nombre}</span>
        <button className="plano icono" title="Quitar cliente" onClick={() => setCliente(null)}>
          ✕
        </button>
      </div>
    );
  }

  async function registrar(nombre: string) {
    setCreando(true);
    setError("");
    try {
      setCliente(await apiTerceros.crear({ nombre, es_cliente: true }));
      setNombreLibre("");
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCreando(false);
    }
  }

  return (
    <div>
      <Autocompletar<Tercero>
        placeholder="Buscar cliente registrado…"
        buscar={async (texto) =>
          (await apiTerceros.listar({ search: texto, es_cliente: true, activo: true })).results.slice(0, 6)
        }
        pintar={(t) => (
          <span>
            <strong>{t.nombre}</strong>
            {t.nit_ci && <span style={{ color: "var(--tenue)" }}> · {t.nit_ci}</span>}
          </span>
        )}
        alElegir={setCliente}
      />
      <input
        style={{ marginTop: 6 }}
        value={nombreLibre}
        placeholder="…o escribe el nombre (mostrador)"
        onChange={(e) => setNombreLibre(e.target.value)}
      />
      {nombreLibre.trim() && (
        <button
          className="plano"
          style={{ marginTop: 6, fontSize: 13 }}
          disabled={creando}
          onClick={() => registrar(nombreLibre.trim())}
        >
          {creando ? "Registrando…" : `Registrar a "${nombreLibre.trim()}" como cliente`}
        </button>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

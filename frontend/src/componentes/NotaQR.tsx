/*
  El QR de la nota de venta, tal como lo ve el vendedor.

  Flujo pensado para el mostrador: se cobra, aparece este bloque y el cliente
  escanea con la cámara. En su celular se abre la nota y desde ahí él decide si
  la guarda en la galería, la manda por WhatsApp o la imprime. Si el cliente
  registrado tiene WhatsApp, el vendedor puede además enviársela de una vez.
*/

import { useState } from "react";

import type { Tercero, Venta } from "../api/tipos";
import { dinero } from "../util/formato";

/** Normaliza a formato internacional. En Bolivia los móviles son 8 dígitos. */
function numeroWhatsapp(cliente?: Tercero | null): string | null {
  const contacto = cliente?.contactos?.find((c) => c.tipo === "whatsapp" || c.tipo === "telefono");
  if (!contacto) return null;
  const digitos = contacto.valor.replace(/\D/g, "");
  if (!digitos) return null;
  return digitos.length === 8 ? `591${digitos}` : digitos;
}

export function NotaQR({ venta, cliente }: { venta: Venta; cliente?: Tercero | null }) {
  const [aviso, setAviso] = useState("");

  const texto =
    `Nota de venta ${venta.numero}\n` +
    `Total: ${dinero(venta.total)}\n` +
    `Puedes verla, guardarla o descargarla aquí:\n${venta.url_publica}`;
  const numero = numeroWhatsapp(cliente);
  const enlaceWsp = `https://wa.me/${numero ?? ""}?text=${encodeURIComponent(texto)}`;

  async function copiar() {
    try {
      await navigator.clipboard.writeText(venta.url_publica);
      setAviso("Link copiado.");
    } catch {
      setAviso(venta.url_publica);
    }
  }

  return (
    <div className="qr-caja">
      <img src={venta.url_qr} alt={`Código QR de la nota ${venta.numero}`} />
      <div className="acciones-nota">
        <p style={{ margin: 0, fontSize: 13, color: "var(--tenue)" }}>
          El cliente escanea y se lleva su nota: puede <strong>guardarla en su galería</strong>,
          mandarla por WhatsApp o imprimirla.
        </p>
        <a className="boton primario" href={venta.url_publica} target="_blank" rel="noreferrer">
          Abrir la nota
        </a>
        <a className="boton" href={enlaceWsp} target="_blank" rel="noreferrer">
          Enviar por WhatsApp{numero ? "" : " (elegir contacto)"}
        </a>
        <button onClick={copiar}>Copiar el link</button>
        <span className="enlace-corto">{venta.url_publica}</span>
        {aviso && <span style={{ fontSize: 12, color: "var(--acento)" }}>{aviso}</span>}
      </div>
    </div>
  );
}

/*
  Entrada al panel. Dos modos en una sola pantalla: iniciar sesión y registrar un
  negocio nuevo (que crea usuario + organización + membresía de propietario en
  una sola llamada, ver RegistroSerializer en el backend).

  A la izquierda cuenta qué es Kinemart (en el celular, solo el titular); a la
  derecha, el formulario. Lo que se promete ahí tiene que ser cierto hoy.
*/

import { useState, type FormEvent } from "react";
import axios from "axios";

import { URL_API, mensajeDeError } from "../api/cliente";
import { useSesion } from "../auth/sesion";
import { IconoOjo } from "../componentes/Iconos";
import { Logo, SelectorTema } from "../componentes/Tema";
import { Campo, Error } from "../componentes/ui";

export function Login() {
  const { entrar } = useSesion();
  const [registrando, setRegistrando] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verClave, setVerClave] = useState(false);
  const [nombreCompleto, setNombreCompleto] = useState("");
  const [negocio, setNegocio] = useState("");
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setOcupado(true);
    setError("");
    try {
      if (registrando) {
        await axios.post(`${URL_API}/api/registro/`, {
          email,
          password,
          nombre_completo: nombreCompleto,
          nombre_organizacion: negocio,
        });
      }
      await entrar(email, password);
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="pantalla-login">
      <div className="halo" aria-hidden="true" />

      <header className="cabeza-login">
        <Logo alto={30} />
        <SelectorTema compacto />
      </header>

      <section className="relato">
        <h1>
          Abre la tienda.
          <span className="segunda">El resto lo anotamos.</span>
        </h1>
        <p>
          Ventas, cotizaciones y catálogo en un solo lugar. Cada venta sale con su
          nota y su QR para que tu cliente la guarde o la mande por WhatsApp.
        </p>
        <div className="muestras">
          <div>
            <strong>QR</strong>
            <small>en cada nota de venta</small>
          </div>
          <div>
            <strong>Celular o PC</strong>
            <small>la misma cuenta en los dos</small>
          </div>
          <div>
            <strong>Precio mínimo</strong>
            <small>te avisa antes de vender bajo el piso</small>
          </div>
        </div>
      </section>

      <form onSubmit={enviar}>
        <h2>{registrando ? "Registra tu negocio" : "Entrar"}</h2>
        <p className="sub">
          {registrando
            ? "Creamos tu negocio y tu usuario como propietario."
            : "Con el correo de tu negocio."}
        </p>

        <Error>{error}</Error>

        {registrando && (
          <>
            <Campo etiqueta="Nombre del negocio">
              <input value={negocio} onChange={(e) => setNegocio(e.target.value)} required />
            </Campo>
            <Campo etiqueta="Tu nombre">
              <input
                value={nombreCompleto}
                autoComplete="name"
                onChange={(e) => setNombreCompleto(e.target.value)}
              />
            </Campo>
          </>
        )}

        <Campo etiqueta="Correo">
          <input
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </Campo>

        <label className="campo">
          <span>Contraseña</span>
          <div className="clave">
            <input
              type={verClave ? "text" : "password"}
              autoComplete={registrando ? "new-password" : "current-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => setVerClave(!verClave)}
              aria-label={verClave ? "Ocultar contraseña" : "Mostrar contraseña"}
              title={verClave ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              <IconoOjo tachado={verClave} />
            </button>
          </div>
        </label>

        <button className="primario grande" disabled={ocupado} type="submit" style={{ marginTop: 6 }}>
          {ocupado ? "Un momento…" : registrando ? "Crear negocio y entrar" : "Entrar"}
        </button>

        <div className="alterno">
          {registrando ? "¿Ya tienes cuenta?" : "¿Tu negocio aún no usa Kinemart?"}
          <button
            type="button"
            onClick={() => {
              setRegistrando(!registrando);
              setError("");
            }}
          >
            {registrando ? "Entrar" : "Regístralo"}
          </button>
        </div>
      </form>
    </div>
  );
}

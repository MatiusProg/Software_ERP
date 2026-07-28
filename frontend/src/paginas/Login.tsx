/*
  Entrada al panel. Dos modos en una sola pantalla: iniciar sesión y registrar un
  negocio nuevo (que crea usuario + organización + membresía de propietario en
  una sola llamada, ver RegistroSerializer en el backend).
*/

import { useState, type FormEvent } from "react";
import axios from "axios";

import { URL_API, mensajeDeError } from "../api/cliente";
import { useSesion } from "../auth/sesion";
import { InterruptorTema } from "../componentes/Tema";
import { Campo, Error } from "../componentes/ui";

export function Login() {
  const { entrar } = useSesion();
  const [registrando, setRegistrando] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
      <div style={{ position: "fixed", top: 14, right: 16 }}>
        <InterruptorTema />
      </div>
      <form className="tarjeta" onSubmit={enviar}>
        <h1>{registrando ? "Crear tu negocio" : "Entrar al panel"}</h1>
        <p className="sub">
          {registrando
            ? "Se crea tu negocio y tu usuario como propietario."
            : "Sistema ERP · ventas, cotizaciones y catálogo."}
        </p>

        <Error>{error}</Error>

        {registrando && (
          <>
            <Campo etiqueta="Nombre del negocio">
              <input value={negocio} onChange={(e) => setNegocio(e.target.value)} required />
            </Campo>
            <Campo etiqueta="Tu nombre">
              <input value={nombreCompleto} onChange={(e) => setNombreCompleto(e.target.value)} />
            </Campo>
          </>
        )}

        <Campo etiqueta="Correo">
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </Campo>
        <Campo etiqueta="Contraseña">
          <input
            type="password"
            autoComplete={registrando ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </Campo>

        <button className="primario grande" disabled={ocupado} type="submit">
          {ocupado ? "Un momento…" : registrando ? "Crear negocio y entrar" : "Entrar"}
        </button>

        <button
          type="button"
          className="plano"
          style={{ width: "100%", marginTop: 10 }}
          onClick={() => {
            setRegistrando(!registrando);
            setError("");
          }}
        >
          {registrando ? "Ya tengo cuenta" : "Registrar un negocio nuevo"}
        </button>
      </form>
    </div>
  );
}

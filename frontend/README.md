# Panel ERP (React + TypeScript)

Panel web del sistema: punto de venta, catálogo, cotizaciones, listas y clientes.
Consume la API de `backend/` por JWT.

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # comprueba tipos (tsc) y compila a dist/
```

La API se toma de `VITE_API_URL` (por defecto `http://127.0.0.1:8000`).
Copia `.env.example` a `.env` si la tuya está en otra dirección. El backend debe
tener ese origen en `CORS_ALLOWED_ORIGINS`.

## Cómo está organizado

```
src/
├─ api/
│  ├─ cliente.ts      # axios, tokens JWT y reintento automático ante 401
│  ├─ recursos.ts     # llamadas por recurso + gancho useLista
│  └─ tipos.ts        # lo que devuelve la API
├─ auth/sesion.tsx    # quién está dentro, su organización, su rol y permisos
├─ componentes/       # piezas compartidas (modal, buscador, editor de líneas, QR)
├─ paginas/           # una por sección del menú
├─ util/formato.ts    # dinero, cantidades y fechas
└─ estilos.css        # variables de tema (claro/oscuro) y estilos
```

### Decisiones

- **Sin librería de estado de servidor**: axios + el gancho `useLista` alcanzan
  para las pantallas que hay; menos dependencias que mantener.
- **`access` en memoria, `refresh` en localStorage**: si roban el localStorage no
  se llevan un token de acceso vivo. Al recargar la página se pide uno nuevo.
- **Los totales se calculan en el backend**: lo que ves mientras armas la venta es
  una vista previa; el IVA definitivo lo devuelve la API para no tener la misma
  regla escrita en dos lugares.
- **Tema claro/oscuro**: se aplica en `index.html` antes de pintar (sin destello)
  y los componentes solo leen variables CSS.

### Atajos del punto de venta

| Tecla | Qué hace |
|---|---|
| `Enter` en el buscador | agrega el primer producto sugerido (o el texto libre) |
| `F2` | vuelve al buscador desde cualquier campo |
| `Esc` | cierra el modal abierto |

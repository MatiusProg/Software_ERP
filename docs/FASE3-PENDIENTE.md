# Fase 3 — Traspaso para continuar (bloques 2 y 3 del frontend)

> Documento de continuación. Escrito al cerrar la sesión del **2026-07-17**.
> El **backend de Fase 3 está terminado, probado y commiteado** (`de79be7` en `main`,
> **sin push todavía**). Falta solo el frontend: el **panel React** y **conectar la PWA**.

---

## 1. Estado actual (qué YA está hecho)

- **App `ventas`** (`backend/apps/ventas/`): Cotización, Venta y Lista (cabecera + detalle).
  - Doble modo de línea: `total` directo (default) o `cantidad × precio_unitario` (opt-in).
  - Correlativos por organización (`V-0001`, `COT-0001`) con contador atómico por tenant.
  - Precio congelado en la línea; **IVA incluido** con desglose (`impuesto_total`, `impuesto_monto`).
  - Cliente opcional (FK `Tercero`) + `cliente_nombre` libre para mostrador.
  - Venta editable pero **auditada** (Venta/VentaDetalle/Cotizacion en la bitácora).
  - Acción `convertir_en_venta` (cotización → venta).
- **App `tienda`** (`backend/apps/tienda/`): escaparate público de solo-lectura por `slug`, sin login.
- **40 pruebas en verde** (17 Fase 2 + 16 ventas + 7 tienda).
- Docs al día: `README.md`, `backend/README.md`, `docs/PLAN.md`.

**Pendiente de Fase 3:** (2) panel **React** · (3) conectar la **PWA**.
**Al cerrar la fase:** migrar la BD a **Supabase** + desplegar en **Railway** (ver §5).

---

## 2. Referencia rápida de la API (para el frontend)

Base local: `http://127.0.0.1:8000`. Paginación global **25/página**
(`?page=`, `count`, `results`), búsqueda `?search=`, orden `?ordering=`.

### Autenticación (JWT)
| Acción | Método y ruta | Body | Devuelve |
|---|---|---|---|
| Registrar negocio | `POST /api/registro/` | `{email, password, nombre_completo, nombre_organizacion}` | crea usuario + organización + membresía propietario |
| Login | `POST /api/auth/token/` | `{email, password}` | `{access, refresh}` (login auditado) |
| Refrescar token | `POST /api/auth/token/refresh/` | `{refresh}` | `{access}` |
| Perfil activo | `GET /api/yo/` | — | perfil, `organizacion_activa`, `rol_activo` |

Rutas protegidas: header `Authorization: Bearer <access>`.
Si el usuario pertenece a varias organizaciones, puede elegir con el header
`X-Organization: <slug>` (por defecto se resuelve su membresía).

### Recursos protegidos (Fase 2 y 3)
| Recurso | Ruta | Filtros | Búsqueda |
|---|---|---|---|
| Categorías | `/api/categorias/` | — | nombre, descripción |
| Productos | `/api/productos/` (+ `/{id}/historial_precios/`) | categoria, unidad, es_servicio, activo | sku, código, nombre |
| Terceros | `/api/terceros/` | es_cliente, es_proveedor, es_transportadora, activo | — |
| Cotizaciones | `/api/cotizaciones/` (+ `/{id}/convertir_en_venta/`) | estado, cliente | numero, cliente_nombre |
| Ventas | `/api/ventas/` | estado, estado_pago, cliente | numero, cliente_nombre |
| Listas | `/api/listas/` | estado, cliente | titulo, cliente_nombre |

### Escaparate público (sin login)
- `GET /api/tienda/<slug>/` — datos del negocio.
- `GET /api/tienda/<slug>/productos/` — catálogo (filtros: categoria, es_servicio; search: nombre, sku, código).
- `GET /api/tienda/<slug>/categorias/`.

### Forma de una línea (ventas/cotizaciones = `detalles`; listas = `items`)
```jsonc
{
  "producto": null,            // opcional: id de un Producto del catálogo
  "descripcion": "Coca 2L",    // requerido si no hay producto
  "detalle": "1 java",         // empaque/nota libre (opcional)
  // Modo directo (default): mandar total
  "total": "113.00",
  // Modo unitario (opt-in): mandar estos dos y el total se calcula
  "cantidad": "15",
  "precio_unitario": "20.00",
  "impuesto": "13.00"          // solo ventas/cotizaciones; listas no llevan impuesto
  // "comprado": true          // solo items de lista
}
```

### Permisos por rol
| Recurso | Leer | Crear/editar | Borrar |
|---|---|---|---|
| Categorías, Productos | cualquier miembro | propietario, admin | propietario, admin |
| Terceros, **Ventas, Cotizaciones, Listas** | cualquier miembro | propietario, admin, **vendedor** | propietario, admin |

---

## 3. BLOQUE 2 — Panel ERP en React

**Decisiones ya cerradas:** stack **Vite + React + TypeScript** (elección de largo plazo).
La PWA de listas se queda en vanilla como cliente ligero (ver §4).

### Pasos sugeridos
1. **Crear el proyecto** en `frontend/` (no tocar la PWA de la raíz):
   `npm create vite@latest frontend -- --template react-ts`
2. Librerías recomendadas: **React Router** (rutas), **TanStack Query** + **axios**
   (datos/estado servidor), y dejar el diseño/tema para después (ver
   [[frontend-discussion-pending]] — animaciones/temas se discuten aquí).
3. **Auth**: guardar `access` (memoria/estado) y `refresh` (localStorage). Interceptor
   axios que, ante 401, llame a `/api/auth/token/refresh/` y reintente. Añadir el
   header `Authorization` en cada request.
4. **CORS**: habilitar `django-cors-headers` en el backend para `http://localhost:5173`
   (el dev server de Vite). *(Aún no está instalado — es el primer cambio de backend
   que tocará mañana.)*
5. **Pantallas MVP** (en este orden, para poder probar Fase 3 cuanto antes):
   1. **Login** → contra `/api/auth/token/`, luego `GET /api/yo/` para nombre/rol/org.
   2. **Productos** — listar/crear/editar (reusa Fase 2; valida que el CRUD + JWT funcionan).
   3. **Venta (POS)** — buscar producto, armar `detalles` (modo directo y unitario),
      cliente opcional, ver totales/IVA, guardar → muestra `numero`. **Este es el objetivo.**
   4. **Cotizaciones** — igual que venta + botón "convertir en venta".
   5. **Listas** — CRUD simple (y sirve de espejo de lo que sincroniza la PWA).
6. **Terceros** — selector de cliente reutilizable (crear al vuelo desde la venta).

> Nota: la venta guarda `total`/`impuesto_total`/`subtotal` **calculados en el backend**;
> el front solo manda las líneas y muestra lo que devuelve. No dupliques el cálculo de IVA.

---

## 4. BLOQUE 3 — Conectar la PWA (modo local ↔ conectado)

**Principio (no romper):** el modo **local sigue igual** — sin login, guardado en el
dispositivo. Registrarse **suma** (sincronizar, respaldar), nunca bloquea.

### Cómo funciona la PWA hoy (`index.html` en la raíz, ~712 líneas, todo vanilla)
- Estado en `localStorage` (`STORE_KEY`), JSON con varias **listas**.
- Cada lista: `{ id, name, base, date, items[], quoteNum }`.
- Cada item: `{ id, name, price, quotePrice, done, ... }`
  - `price` = precio real/total de compra · `quotePrice` = precio de cotización
  - `done` = comprado (pendiente vs comprado)
- Dos modos de UI: **compra** (usa `price`, total comprado) y **cotización** (usa `quotePrice`).

### Mapeo a la API (para la sincronización)
| PWA (local) | API (Fase 3) |
|---|---|
| lista (`name`, `items`) | `Lista` (`titulo`) + `ListaItem` |
| item `name` | `ListaItem.descripcion` |
| item `price` (compra) | `ListaItem.total` |
| item `done` | `ListaItem.comprado` |
| modo cotización (`quotePrice` por proveedor) | `Cotizacion` + `CotizacionDetalle` (cliente = proveedor) |

### Plan de sincronización
1. **Añadir login opcional** en la PWA (POST `/api/auth/token/`, guardar tokens).
2. **Al entrar por primera vez**: ofrecer "subir mis listas locales" → crear `Lista`(s)
   vía `POST /api/listas/` con sus `items`. No borrar lo local hasta confirmar.
3. **Sync bidireccional simple** (empezar por *push* local→nube; *pull* después):
   marcar cada lista/item con estado y `updated_at`; resolver conflictos por "gana el
   más reciente" al inicio (simple y suficiente).
4. **Feature pendiente `precio unitario`** ([[pwa-precio-unitario]]): el backend YA
   soporta `cantidad` + `precio_unitario` en la línea. Falta el **opt-in en la UI de la
   PWA**: por defecto se escribe solo el total (como hoy); activar por ítem para que el
   total se calcule `cantidad × precio_unitario`. Útil sobre todo en cotizaciones.

> Ojo con el `service-worker.js`: al cambiar `index.html`, subir la versión del cache
> para que el SW sirva la versión nueva (si no, se queda con la vieja cacheada).

---

## 5. Cierre de Fase 3 — Supabase + Railway (al final, no antes)

Checklist para cuando el frontend ya esté probado (decisión: se hace al cerrar la fase):
1. Crear proyecto en **Supabase**; obtener la cadena de conexión Postgres.
2. Backend: mover credenciales de BD a variables de entorno (ya hay `.env`/`.env.example`);
   apuntar `DATABASES` a Supabase. Correr `migrate`. Verificar las 40 pruebas contra la nueva BD.
3. **Railway**: desplegar el backend (Gunicorn/Uvicorn + `collectstatic`), variables de
   entorno, y `ALLOWED_HOSTS`/CORS de producción.
4. PWA: publicar (GitHub Pages hoy) apuntando a la API de Railway.
5. Revisar el flujo público del escaparate (`/api/tienda/<slug>/...`) en producción.

---

## 6. Recordatorio: levantar y probar (Git Bash)

```bash
source backend/.venv/Scripts/activate
cd backend
python manage.py runserver           # API en http://127.0.0.1:8000
python manage.py test apps.catalogo apps.terceros apps.ventas apps.tienda   # 40 pruebas
```
Superusuario admin: `admin@erp.local` / `291022`. Detalle completo en `backend/README.md`.
```

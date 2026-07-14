# Backend ERP — Guía rápida

Backend Django + DRF, multi-tenant (SaaS). PostgreSQL local en desarrollo.
Comandos pensados para **Git Bash** (tu shell). Notas de PowerShell al final.

## Requisitos ya instalados
- Python 3.14 (venv en `backend/.venv`)
- PostgreSQL 18 (servicio `postgresql-x64-18`, base `erp_dev`)

---

## 1. Activar el entorno (venv) — Git Bash

Desde la raíz del proyecto (`D:/TRABAJO/Sistema_ERP`):

```bash
source backend/.venv/Scripts/activate
```

> Ojo: aquí el entorno se llama `.venv` (con punto) y está dentro de `backend/`,
> no `venv/` como en tus proyectos anteriores. Sabes que está activo cuando ves
> `(.venv)` al inicio de la línea. Para salir: `deactivate`.

---

## 2. Levantar el servidor

```bash
cd backend
python manage.py runserver
```

- Back-office:  http://127.0.0.1:8000/admin/
- API:          http://127.0.0.1:8000/api/...

Detener: `Ctrl + C`.

**Superusuario del admin:** `admin@erp.local` / `291022`

---

## 3. Probar la API manualmente (curl, en Git Bash)

Con el servidor corriendo, en **otra** terminal Git Bash:

### Registrar un negocio nuevo (crea usuario + organización + propietario)
```bash
curl -X POST http://127.0.0.1:8000/api/registro/ \
  -H "Content-Type: application/json" \
  -d '{"email":"prueba@negocio.test","password":"clave12345","nombre_completo":"Prueba","nombre_organizacion":"Negocio Prueba"}'
```

### Login (obtener token JWT — queda registrado en la bitácora)
```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"prueba@negocio.test","password":"clave12345"}'
```
Devuelve `access` y `refresh`. Copia el valor de `access`.

### Ver mi perfil, organización y rol activos (ruta protegida)
```bash
curl http://127.0.0.1:8000/api/yo/ -H "Authorization: Bearer PEGA_AQUI_EL_ACCESS"
```

### Truco: guardar el token en una variable automáticamente
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"prueba@negocio.test","password":"clave12345"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access'])")

curl http://127.0.0.1:8000/api/yo/ -H "Authorization: Bearer $TOKEN"
```
Si `organizacion_activa` NO es null y `rol_activo` es `propietario`, el
aislamiento multi-tenant y los roles funcionan. ✅

### Endpoints de catálogo y terceros (Fase 2)

Todos requieren `Authorization: Bearer $TOKEN`. Todo queda aislado por
organización y auditado. Listados paginados (25/pág) con búsqueda (`?search=`),
filtros y orden (`?ordering=`).

**Permisos por rol:**

| Recurso | Leer | Crear / editar | Borrar |
|---|---|---|---|
| Categorías, Productos | cualquier miembro | propietario, admin | propietario, admin |
| Terceros (clientes) | cualquier miembro | propietario, admin, **vendedor** | propietario, admin |

> El **vendedor** ya ve todos los campos del producto, **incluido el precio de
> venta mínimo** (el piso para negociar). El precio real según cantidad, promo o
> venta de varios productos es lógica de la **Fase 3 (ventas)**, que respeta ese
> mínimo. El vendedor puede registrar clientes (terceros) al vender, pero no
> borrarlos.

```bash
# Categorías
curl http://127.0.0.1:8000/api/categorias/ -H "Authorization: Bearer $TOKEN"
curl -X POST http://127.0.0.1:8000/api/categorias/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"nombre":"Bebidas"}'

# Productos (filtros: categoria, unidad, es_servicio, activo | search: sku, código, nombre)
curl "http://127.0.0.1:8000/api/productos/?search=coca&activo=true" -H "Authorization: Bearer $TOKEN"
curl -X POST http://127.0.0.1:8000/api/productos/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sku":"P001","nombre":"Coca 2L","precio_venta":"12.00","precio_compra":"9.00"}'

# Historial de precios de un producto (se llena solo al cambiar un precio)
curl http://127.0.0.1:8000/api/productos/1/historial_precios/ -H "Authorization: Bearer $TOKEN"

# Terceros (filtros: es_cliente, es_proveedor, es_transportadora, activo)
curl "http://127.0.0.1:8000/api/terceros/?es_proveedor=true" -H "Authorization: Bearer $TOKEN"
curl -X POST http://127.0.0.1:8000/api/terceros/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Distribuidora Sur","es_proveedor":true,
       "contactos":[{"tipo":"telefono","valor":"77712345"}],
       "ubicaciones":[{"direccion":"Av. Siempre Viva 123","ciudad":"Santa Cruz"}]}'
```

---

## 4. Entrar a la base de datos

**Opción GUI (recomendada):** abrir **pgAdmin 4** (menú Inicio) → conectar con
user `postgres` / `291022` → base `erp_dev`.

**Opción Django** (con el venv activo, dentro de `backend`):
```bash
python manage.py dbshell
```

**Opción psql (Git Bash)** — no está en el PATH, por eso la ruta completa:
```bash
"/c/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -h 127.0.0.1 -d erp_dev
```
Dentro: `\dt` (tablas), `SELECT * FROM organizacion;`, `SELECT * FROM bitacora;`,
`\q` (salir). Tablas de dominio en español: `organizacion`, `usuario`,
`membresia`, `bitacora`, `bitacora_detalle`.

---

## 5. Comandos útiles de Django

```bash
python manage.py createsuperuser        # crear otro admin
python manage.py makemigrations         # generar migraciones tras cambiar modelos
python manage.py migrate                # aplicar migraciones
python manage.py test                   # correr todas las pruebas automatizadas
python manage.py test apps.catalogo apps.terceros   # solo catálogo y terceros (Fase 2)
python manage.py shell                  # consola de Python con Django cargado
```

---

## Estructura

```
backend/
├─ config/            # settings, urls, wsgi
├─ apps/
│  ├─ comun/          # base multi-tenant (ModeloTenant, middleware, auth JWT)
│  ├─ cuentas/        # Organizacion, Usuario, Membresia + API (registro, login, yo)
│  └─ auditoria/      # Bitacora + BitacoraDetalle (auditoría automática por señales)
├─ .env               # secretos locales (NO se sube a git)
├─ .env.example       # plantilla
└─ manage.py
```

---

## Nota para PowerShell (si algún día lo usas)

- Activar venv: `.\backend\.venv\Scripts\Activate.ps1`
  (una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)
- Probar API: usar `Invoke-RestMethod` en vez de `curl`.

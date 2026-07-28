# Sistema ERP

Plataforma **ERP SaaS multi-tenant** para pequeños negocios: catálogo, ventas,
cotizaciones, compras e inventario. Nace de una PWA de listas de compras y
cotizaciones, que se convierte en el cliente ligero móvil del sistema.

> Estado: **Fase 3 en curso** — sobre los cimientos multi-tenant (Fase 0), la
> seguridad + auditoría (Fase 1) y el catálogo/terceros (Fase 2), ya están las
> ventas, cotizaciones y listas, el escaparate público, la **nota de venta por QR**
> y el **panel React**. API cubierta por **46 pruebas automatizadas** (en verde).
> Ver el [roadmap](#roadmap).

## Arquitectura

- **Backend:** Django + Django REST Framework + PostgreSQL. API REST con JWT.
  Multi-tenant: cada negocio (organización) tiene sus datos aislados.
- **Panel ERP:** React + TypeScript (Vite) en `frontend/` — punto de venta,
  catálogo, cotizaciones, listas y clientes, con tema claro/oscuro.
- **PWA de listas:** cliente ligero en la raíz, en dos modos (local y conectado).
- **Despliegue previsto:** Railway (backend + Postgres) en producción.

## Estructura del repositorio

```
Sistema_ERP/
├─ backend/            # API Django (ver backend/README.md para levantarlo)
├─ frontend/           # panel ERP en React + TypeScript (Vite)
├─ index.html + PWA/   # PWA de listas de compras (cliente ligero, en la raíz)
└─ docs/               # PLAN.md (documento vivo) y notas de fase
```

> La PWA vive en la raíz porque se publica con GitHub Pages.

## Empezar

**Backend** — guía completa en **[`backend/README.md`](backend/README.md)**:

```bash
source backend/.venv/Scripts/activate
cd backend
python manage.py migrate
python manage.py datos_demo      # catálogo, clientes y ventas de prueba
python manage.py runserver       # http://127.0.0.1:8000
```

**Panel ERP** (en otra terminal):

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Entrar con los usuarios que imprime `datos_demo`
(`demo@erp.test` / `clave12345`, propietario).

## Roadmap

- **Fase 0 — Cimientos multi-tenant** ✅ Organización, Usuario, Membresía, JWT.
- **Fase 1 — Seguridad + Auditoría** ✅ Roles/permisos en la API; bitácora + detalle.
- **Fase 2 — Catálogo y Terceros** ✅ Categorías, Productos (con precios e historial),
  Terceros (cliente/proveedor/transportadora) con contactos y ubicación. (17 pruebas)
- **Fase 3 — Ventas, Cotizaciones y Listas** ⏳ backend + **nota de venta por QR**
  (el cliente escanea y guarda su nota en la galería o la manda por WhatsApp) +
  **panel React**. Falta conectar la PWA y desplegar.
- **Fase 4 — Compras e Inventario** Compras, almacenes y movimientos de stock.
- **Fase 5 — Reportes y Exportables** (PDF A4 y ticket térmico 80mm).
- **Fase 6 — Pagos QR (Bolivia)** — QR Simple del BCB (en investigación).
- **Fase 7 — Monetización + Facturación** — planes de suscripción; SIN si se requiere.

> El roadmap detallado, el modelo de datos y las decisiones técnicas viven en
> [`docs/PLAN.md`](docs/PLAN.md) (documento vivo).

## Autor

Luis Mateo Hurtado Castro — Ingeniería en Sistemas.

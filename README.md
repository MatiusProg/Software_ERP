# Sistema ERP

Plataforma **ERP SaaS multi-tenant** para pequeños negocios: catálogo, ventas,
cotizaciones, compras e inventario. Nace de una PWA de listas de compras y
cotizaciones, que se convierte en el cliente ligero móvil del sistema.

> Estado: **Fase 2 completada** — sobre los cimientos multi-tenant (Fase 0) y la
> seguridad + auditoría (Fase 1) se sumaron el catálogo (categorías, productos con
> precios e historial) y los terceros (cliente/proveedor/transportadora). API
> cubierta por **17 pruebas automatizadas** (todas en verde).
> **Siguiente: Fase 3 (Ventas, Cotizaciones y Listas + conectar la PWA).**
> Ver el [roadmap](#roadmap).

## Arquitectura

- **Backend:** Django + Django REST Framework + PostgreSQL. API REST con JWT.
  Multi-tenant: cada negocio (organización) tiene sus datos aislados.
- **Frontend:** PWA de listas/cotizaciones (actual) + panel ERP (próximamente).
- **Despliegue previsto:** Railway (backend + Postgres) en producción.

## Estructura del repositorio

```
Sistema_ERP/
├─ backend/            # API Django (ver backend/README.md para levantarlo)
├─ index.html + PWA/   # PWA de listas de compras (cliente ligero, en la raíz)
└─ docs/               # documentación (futuro)
```

> La PWA vive por ahora en la raíz porque se publica con GitHub Pages. Cuando se
> construya el frontend del ERP, se moverá a `frontend/` y se reconfigurará Pages.

## Empezar

El backend se levanta siguiendo **[`backend/README.md`](backend/README.md)**
(guía para Git Bash: activar venv, correr el servidor, probar la API, entrar a
la base de datos).

## Roadmap

- **Fase 0 — Cimientos multi-tenant** ✅ Organización, Usuario, Membresía, JWT.
- **Fase 1 — Seguridad + Auditoría** ✅ Roles/permisos en la API; bitácora + detalle.
- **Fase 2 — Catálogo y Terceros** ✅ Categorías, Productos (con precios e historial),
  Terceros (cliente/proveedor/transportadora) con contactos y ubicación. (17 pruebas)
- **Fase 3 — Ventas, Cotizaciones y Listas** ⏳ + conectar la PWA a la API.
- **Fase 4 — Compras e Inventario** Compras, almacenes y movimientos de stock.
- **Fase 5 — Reportes y Exportables** (PDF A4 y ticket térmico 80mm).
- **Fase 6 — Pagos QR (Bolivia)** — QR Simple del BCB (en investigación).
- **Fase 7 — Monetización + Facturación** — planes de suscripción; SIN si se requiere.

> El roadmap detallado, el modelo de datos y las decisiones técnicas viven en
> [`docs/PLAN.md`](docs/PLAN.md) (documento vivo).

## Autor

Luis Mateo Hurtado Castro — Ingeniería en Sistemas.

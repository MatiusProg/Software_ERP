# Sistema ERP

Plataforma **ERP SaaS multi-tenant** para pequeños negocios: catálogo, ventas,
cotizaciones, compras e inventario. Nace de una PWA de listas de compras y
cotizaciones, que se convierte en el cliente ligero móvil del sistema.

> Estado: **Fase 0 completada** — cimientos multi-tenant del backend (auth,
> organizaciones, usuarios y roles). Ver el [roadmap](#roadmap).

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
- **Fase 1 — Catálogo** Productos, Categorías, Terceros (clientes/proveedores).
- **Fase 2 — Ventas y Cotizaciones** + conectar la PWA a la API.
- **Fase 3 — Inventario** Almacenes y movimientos de stock.
- **Fase 4 — Auditoría, reportes y dashboard.**

## Autor

Luis Mateo Hurtado Castro — Ingeniería en Sistemas.

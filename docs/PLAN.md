# Plan del Sistema ERP

Documento vivo del proyecto. Resume visión, arquitectura, decisiones y roadmap.
Última actualización: 2026-07-13.

---

## 1. Visión

ERP **SaaS multi-tenant** para pequeños negocios (Bolivia). Cada negocio
(organización) tiene sus datos aislados. Nace de una PWA de listas de compras y
cotizaciones, que se conserva como **cliente ligero**.

Doble público:
- Uso personal/simple: listas y cotizaciones, **sin login** (modo local).
- Clientes de pago: ERP completo con login, roles y auditoría (modo conectado).

## 2. Arquitectura

- **Backend:** Django + Django REST Framework + PostgreSQL. API REST con JWT.
- **Multi-tenant:** modelo `Organizacion` + FK en cada tabla de negocio +
  scoping forzado por manager/middleware. Aislamiento por defecto.
- **Frontend:** PWA (listas/cotizaciones) en dos modos (local / conectado);
  panel ERP web (a definir: React) más adelante.
- **Producción:** Railway (backend + Postgres). Supabase queda como opción.

## 3. Decisiones clave

1. **Nombres en español** en todo el dominio (apps, modelos, tablas, campos)
   para legibilidad y colaboradores. Solo el framework Django queda en inglés.
2. **Auditoría en 2 tablas**: `bitacora` (cabecera del evento) + `bitacora_detalle`
   (un registro por campo cambiado, con valor anterior/nuevo). Se llena sola por
   señales de Django + thread-local del usuario actual.
3. **Auditoría y permisos van primero** (Fase 1), antes que los módulos de
   negocio, para que todo nazca auditado y protegido.
4. **PWA doble modo**: local (sin login) y conectado (sincroniza con la API).
5. **Impresión**: notas en formato **ticket térmico 80mm (ESC/POS)** —
   impresora barata y estándar— además de PDF A4 para reportes.
6. **Terceros con roles múltiples**: un tercero puede ser cliente y proveedor a la
   vez → flags `es_cliente` / `es_proveedor` / `es_transportadora` en lugar de un
   único campo `tipo` (evita duplicar el mismo tercero).
7. **CRUD con ViewSets**: desde la Fase 2 la API usa `ModelViewSet` + router DRF,
   con paginación global, `django-filter` y búsqueda/orden. Base común
   `TenantModelViewSet` (queryset scopeado al tenant + permisos por rol).

## 4. Roadmap por fases

| Fase | Módulo | Contenido | Estado |
|---|---|---|---|
| 0 | Cimientos multi-tenant | Organizacion, Usuario, Membresia, JWT, base tenant | ✅ |
| 1 | Seguridad + Auditoría | Refactor a español; roles/permisos en la API; bitácora + detalle | ✅ |
| 2 | Catálogo y Terceros | Categoría, Producto (con precios mín/máx), Historial de precios, Tercero (cliente/proveedor/transportadora) con ubicación y contactos | ⏳ siguiente |
| 3 | Ventas, Cotizaciones y Listas | Cotización, Venta (nota de venta), Lista de pendientes; **conectar la PWA** | pendiente |
| 4 | Compras e Inventario | Compra (nota de compra), Almacén, Movimientos de stock | pendiente |
| 5 | Reportes y Exportables | Reportes de ventas; exportar PDF (listas, notas A4 y ticket 80mm) | pendiente |
| 6 | Pagos QR (Bolivia) | Integración QR (QR Simple BCB vía banco/agregador) — requiere investigación y acuerdo comercial | investigación |
| 7 | Monetización + Facturación | Planes/suscripción de tenants; facturación electrónica (SIN) si el cliente lo pide | futuro |

## 5. Modelo de datos (bosquejo, en español)

**cuentas (seguridad/tenancy)**
- `organizacion` — el tenant.
- `usuario` — login por email, sin username.
- `membresia` — usuario ↔ organización, con `rol` (propietario/admin/vendedor/lectura).

**auditoria**
- `bitacora` — organizacion, usuario, accion, modelo, objeto_id, objeto_desc, ip, user_agent, fecha.
- `bitacora_detalle` — bitacora, campo, valor_anterior, valor_nuevo.

**catalogo**
- `categoria` — nombre, descripción. `sku`/`nombre` únicos **por organización**.
- `producto` — sku, `codigo_barras` (opcional, único por org, indexado — POS/escáner),
  nombre, categoria, unidad, `es_servicio` (bool: servicio sin stock),
  `precio_venta`, `precio_venta_minimo`, `precio_compra`, `precio_compra_maximo`,
  `stock`, `impuesto` (IVA 13% por defecto), `activo` (soft-delete). `sku` único por
  organización. Validación: `precio_venta_minimo ≤ precio_venta` y
  `precio_compra ≤ precio_compra_maximo`. El `stock` es un decimal editable simple en
  esta fase; en la Fase 4 pasa a ser la suma cacheada de `movimiento_stock` (patrón de
  triggers de stock visto en el POS de referencia). `codigo_barras` y `es_servicio`
  provienen de aprendizajes del POS real (ver [[repos-referencia-previos]]).
- `historial_precio` — producto, tipo (venta/compra/min/max), valor, fecha, usuario.
  Se **llena solo por señal** cuando cambia algún precio del producto (para reportes
  de precios; la bitácora es aparte, para cumplimiento).
- `tercero` — nombre, nit_ci (opcional, no único global), notas, `activo`,
  y flags `es_cliente` / `es_proveedor` / `es_transportadora` (ver decisión 6).
- `contacto_tercero` — tercero, tipo (teléfono/email/whatsapp), valor.
- `ubicacion_tercero` — tercero, direccion, ciudad, referencia, lat, lng.

**ventas**
- `cotizacion` + `cotizacion_detalle`.
- `venta` + `venta_detalle` (estado de pago).
- `lista` + `lista_item` (listas de pendientes; puente con la PWA).

**compras**
- `compra` + `compra_detalle`.

**inventario**
- `almacen` — nombre, ubicación.
- `movimiento_stock` — producto, almacen, tipo (entrada/salida/ajuste), cantidad, referencia, fecha, usuario.

**pagos**
- `pago` — venta, metodo (qr/efectivo/transferencia), monto, estado, referencia_qr, fecha.

> Todas las tablas de negocio heredan de `TenantModel` (FK `organizacion` +
> created/updated) y quedan auditadas automáticamente.

## 6. Temas que requieren investigación / decisión futura

- **Pagos QR Bolivia**: el estándar es el **QR Simple interoperable del BCB**.
  La integración suele ir por la API de un banco o un agregador, y normalmente
  exige una cuenta empresarial / acuerdo. A investigar antes de la Fase 6.
- **Impresora**: recomendación inicial → térmica **80mm ESC/POS USB** (barata y
  estándar para notas/tickets). La **facturación electrónica (SIN)** es un
  trámite/integración aparte; se aborda solo si un cliente la exige (Fase 7).
- **Frontend del panel ERP**: React (recomendado por experiencia y portafolio)
  vs. seguir vanilla. Se decide al llegar a la Fase 3.

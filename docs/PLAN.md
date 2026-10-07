# Plan del Sistema ERP

Documento vivo del proyecto. Resume visión, arquitectura, decisiones y roadmap.
Última actualización: 2026-07-16.

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
8. **Escaparate público (app `tienda`)**: endpoints anónimos de solo-lectura que
   exponen el catálogo de un negocio por su `slug` (`/api/tienda/<slug>/productos/`),
   sin login y sin costos/mínimos/stock. Es la base del doble modo: mirar no exige
   cuenta; registrarse suma funciones. El aislamiento aquí viene del `slug`, no del
   tenant activo (se usa el manager `todos` + filtro explícito por organización).
9. **Nota de venta por QR**: cada `Venta` lleva un `token_publico` (UUID4) con el
   que se genera un QR. El cliente lo escanea y abre `/nota/<token>/`: una página
   pública, sin login, desde la que puede **guardar la nota como imagen en su
   galería**, **enviarla por WhatsApp** o **imprimirla/PDF**. El link es
   impredecible (no usa el id secuencial) y solo muestra lo que ya está en el papel
   del cliente. La página es autocontenida (canvas + Web Share API, sin CDN) y el
   QR se genera en el servidor como matriz de módulos, servible en SVG — el mismo
   dato servirá para imprimirlo en el ticket térmico de la Fase 5.
10. **El precio mínimo se respeta al vender**: si una línea con producto del
   catálogo va por debajo de `precio_venta_minimo`, la API responde **400** y solo
   acepta el documento si vuelve con `autorizar_precio_bajo=true`. El documento
   queda marcado (`bajo_minimo`) y se puede filtrar, para revisar después quién
   negoció bajo el piso. Aplica a ventas y cotizaciones (cotizar bajo el mínimo es
   prometer venderlo así). En modo directo, sin cantidad, se asume 1 unidad: es lo
   conservador, evita falsos avisos cuando el total es de varias unidades.
11. **Infraestructura de bajo costo, con techo de gasto** (2026-10-06).
   - **Base de datos:** Supabase free, proyecto `kinemart` en la organización
     *ArmonIA*, región us-east-1. Django se conecta por el **Session pooler
     (5432)**.
   - **API:** Railway Hobby (la cuenta de Karen, compartida), construida con
     `backend/Dockerfile`, en modo serverless y con 2 workers.
   - **Techo de gasto en Railway:** límite duro de **$10**, que es el mínimo
     que permite Railway, y aviso por correo en $5. Si se llega al límite,
     Railway **apaga** los servicios en vez de cobrar.
   - **Por qué así:** en otro proyecto, Railway con Postgres propio pasó los $5
     del Hobby y quedó deuda. Railway cobra la RAM encendida aunque nadie use la
     app.
   - **Riesgos aceptados mientras no haya cliente que pague:**
     - Supabase free se pausa a los 7 días sin actividad. Lo mitiga un workflow
       programado en GitHub Actions.
     - Supabase free no hace respaldos. Lo mitiga un `pg_dump` nocturno en
       GitHub Actions.
   - **Cuándo revisar esta decisión:** cuando entre el primer cliente que paga, o
     si el consumo de Railway se acerca al límite.
     - Base: Supabase Pro ($25, sin pausa, con respaldos diarios) o Postgres en
       Railway.
     - Mudarse cuesta poco: se cambia solo `DATABASE_URL`, sin tocar código ni
       migraciones.
     - Antes de mudar la API, subir el límite duro, para que Railway no la
       apague en plena venta.
     - **Con el primer cliente que paga, apagar Serverless.** Despertar cuesta
       ~1.3 s extra en la primera petición tras 10 min sin uso (medido el
       2026-10-06). Siempre prendida cuesta unos $2–3 al mes, y la primera
       venta ya lo cubre.
   - **Dominio:** cuando esté el de ArmonIA, el panel va en `kinemart.<dominio>`
     (Cloudflare Pages) y la API en `api.kinemart.<dominio>` (dominio propio en
     Railway), con el DNS en Cloudflare. **Las notas reales tienen que salir ya
     con el dominio definitivo**, porque el QR impreso apunta a él para siempre.
12. **Data API de Supabase apagada; RLS pendiente** (2026-10-06).
   - **El problema:** Supabase publica por REST (PostgREST, con la clave *anon*,
     que es pública) todas las tablas del esquema `public`. Django crea ahí sus
     27 tablas sin RLS, incluida `usuarios` con los hashes de contraseña.
   - **Lo que se hizo:** el ERP no usa esa API (Django se conecta directo a
     Postgres), así que se **apagó** en *Integrations → Data API*. Storage (S3)
     no depende de ella.
   - **Es temporal:** hay que activar RLS con `ENABLE` + `FORCE` y políticas por
     `organizacion_id`, conectando Django con un rol sin `BYPASSRLS`. Es el patrón
     ya probado en PROYECTO_MEDICOS (Si2): sus siete reglas están en el README de
     ese repo.
   - **Cuándo:** junto con los planes por tenant y antes de la Fase 4.
   - **Si algún día se vuelve a prender la Data API** (por ejemplo, para
     Realtime), tiene que ser **después** de tener RLS en todas las tablas.

## 4. Roadmap por fases

| Fase | Módulo | Contenido | Estado |
|---|---|---|---|
| 0 | Cimientos multi-tenant | Organizacion, Usuario, Membresia, JWT, base tenant | ✅ |
| 1 | Seguridad + Auditoría | Refactor a español; roles/permisos en la API; bitácora + detalle | ✅ |
| 2 | Catálogo y Terceros | Categoría, Producto (con precios mín/máx), Historial de precios, Tercero (cliente/proveedor/transportadora) con ubicación y contactos | ✅ (17 pruebas) |
| 3 | Ventas, Cotizaciones y Listas | Cotización, Venta (nota de venta) **con QR público**, Lista de pendientes; **panel React**; **PWA conectada** | ⏳ falta desplegar |
| 4 | Compras e Inventario | Compra (nota de compra), Almacén, Movimientos de stock | pendiente |
| 5 | Reportes y Exportables | Reportes de ventas; exportar PDF (listas, notas A4 y ticket 80mm) | pendiente |
| 6 | Pagos QR (Bolivia) | Integración QR (QR Simple BCB vía banco/agregador) — requiere investigación y acuerdo comercial | investigación |
| 7 | Monetización + Facturación | Planes/suscripción de tenants; facturación electrónica (SIN) si el cliente lo pide | futuro |

> **Fase 3 en curso:** backend (apps `ventas` y `tienda`), **nota de venta por QR**,
> **panel React** (`frontend/`) y **PWA conectada** ya están hechos y probados
> (**46 pruebas** en verde). Falta solo **desplegar**: ver
> **[`DESPLIEGUE.md`](DESPLIEGUE.md)**. El detalle de cómo se construyó está en
> **[`FASE3-PENDIENTE.md`](FASE3-PENDIENTE.md)**.

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

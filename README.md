# Sistema ERP

Plataforma **ERP SaaS multi-tenant** para pequeños negocios de Bolivia:
catálogo, punto de venta, cotizaciones, **notas de venta con QR**, y en camino
inventario multisucursal con lotes, compras y reportes. Nació como una PWA de
listas de compras y cotizaciones, que se conserva como cliente ligero.

Proyecto individual de **Luis Mateo Hurtado Castro** — no es un proyecto de la
universidad: tiene un cliente real con dos sucursales esperando usarlo.

> **Repositorio público, datos ficticios.** Ni en `datos_demo`, ni en capturas,
> ni en las pruebas hay datos de clientes reales. Las credenciales viven solo en
> `backend/.env` (fuera de git) y en las variables de Railway.

---

## Dónde está desplegado

| Qué | Enlace |
|---|---|
| **API + notas QR** | <https://api-production-6462.up.railway.app> — dominio provisional de Railway |
| Comprobación rápida de que la API responde | <https://api-production-6462.up.railway.app/admin/login/> |
| **Panel ERP** | ⏳ por publicar (hoy se usa en local contra la API de producción) |
| **PWA de listas** | GitHub Pages, desde la raíz de este repo |
| Repositorio | <https://github.com/MatiusProg/Software_ERP> |

La API corre en **Railway**, construida desde [`backend/Dockerfile`](backend/Dockerfile)
—la misma imagen que levanta `docker compose` en local— y la base de datos es
**Supabase**. El paso a paso, con las variables y las trampas conocidas, está en
[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

> **El plan gratuito de Supabase se pausa a los 7 días sin actividad** y el
> sistema queda caído sin aviso. Un workflow de GitHub Actions lo mantiene
> despierto; aun así, antes de una demostración, entrar al panel y comprobar que
> el proyecto está activo.

---

## En qué vamos

| Fase | Módulo | Estado |
|---|---|---|
| 0 | Cimientos multi-tenant — organización, usuario, membresía, JWT | ✅ |
| 1 | Seguridad + auditoría — roles y permisos en la API, bitácora con detalle por campo | ✅ |
| 2 | Catálogo y terceros — productos con precios e historial; clientes, proveedores, transportadoras | ✅ |
| 3 | Ventas, cotizaciones y listas — **nota de venta por QR**, panel React, PWA conectada | ✅ código · ⏳ despliegue |
| — | **Infraestructura** — Docker, CI en GitHub Actions, despliegue en Railway + Supabase | ⏳ **en curso** |
| — | Planes por tenant, webhooks y **PWA instalable del panel** (el cliente usa iPhone) | siguiente |
| 4 | Compras e inventario — stock por **(producto, sucursal, lote)**, vencimientos, proveedores, código de barras | pedido por el cliente |
| 5 | Reportes y exportables — PDF A4 y ticket térmico 80 mm | pendiente |
| 6 | Pagos QR (Bolivia) — QR Simple del BCB | investigación |
| 7 | Monetización y facturación — suscripciones; SIN si un cliente lo exige | futuro |

El roadmap completo, el modelo de datos y cada decisión con su porqué viven en
[docs/PLAN.md](docs/PLAN.md). Dónde se quedó la última sesión:
[docs/SIGUIENTE-SESION.md](docs/SIGUIENTE-SESION.md).

---

## Tecnologías

| Capa | Herramienta | Versión |
|---|---|---|
| Backend | Django + Django REST Framework | Django **6.0** · DRF 3.17 |
| Lenguaje del backend | Python | **3.13** (la de la imagen Docker) |
| Autenticación | JWT — `djangorestframework-simplejwt` | 5.5 |
| Base de datos | PostgreSQL | **17** (local en Docker y en Supabase) |
| Controlador de base de datos | psycopg | **3.3** (no psycopg2) |
| Panel web | React + TypeScript + Vite | React **19.2** · TS 6 · Vite 8 |
| Lint del panel | oxlint | 1.x |
| PWA de listas | HTML + JS sin framework + service worker | — |
| Contenedores | Docker + Compose | Engine 29 · Compose v5 |
| Hospedaje de la API | Railway — builder `DOCKERFILE` | plan Hobby |
| Base gestionada | Supabase — *Session pooler*, puerto 5432 | plan free |

Las versiones exactas del backend están fijadas en
[`backend/requirements.txt`](backend/requirements.txt). SimpleJWT declara soporte
oficial hasta Django 5.2; aquí corre sobre Django 6.0. Las 55 pruebas pasan
por el login real y comprueban que sin token se responde 401, pero **el refresco
de tokens no tiene prueba**. Si algo falla en la autenticación al actualizar, es
lo primero a mirar.

---

## Arranque rápido

Requisitos: **Docker Desktop** y **Node 22+**. No hace falta Python ni
PostgreSQL instalados: el backend corre en contenedores.

```bash
git clone https://github.com/MatiusProg/Software_ERP.git
cd Software_ERP

cp backend/.env.example backend/.env      # completar DJANGO_SECRET_KEY
docker compose up -d                      # PostgreSQL 17 + API en :8000
docker compose exec api python manage.py datos_demo

cd frontend
npm install
npm run dev                               # panel en http://localhost:5173
```

Usuarios de prueba que crea `datos_demo`:

| Rol | Correo | Contraseña |
|---|---|---|
| Propietario | `demo@erp.test` | `clave12345` |
| Vendedor | `vendedor@erp.test` | `clave12345` |

Verificación de que el entorno quedó bien:

```bash
# 1. Los dos contenedores arriba, la base "healthy".
docker compose ps

# 2. La API responde y el login devuelve tokens.
curl -s -X POST localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@erp.test","password":"clave12345"}'

# 3. Las pruebas pasan (crean y destruyen su propia base).
docker compose exec api python manage.py test
```

El código de `backend/` está montado dentro del contenedor: al guardar un
archivo, Django se recarga solo. Solo hay que reconstruir
(`docker compose up -d --build`) cuando cambia `requirements.txt`.

La base del compose se ve desde fuera (pgAdmin, DBeaver) en `localhost:5440`,
usuario y contraseña `erp`. El 5432/5433 los deja libres para un PostgreSQL
instalado en Windows.

Para levantarlo **sin Docker**, con un venv y Postgres local:
[backend/README.md](backend/README.md).

---

## Las reglas que sostienen el sistema

Romper cualquiera de estas no produce un error: produce **datos equivocados**,
que es peor.

**1. Toda consulta de negocio se filtra por la organización del request.**
Las vistas heredan de `TenantModelViewSet`, que vuelve a filtrar en cada
`get_queryset()`. No alcanza con el manager: el `queryset` de clase de un
ViewSet se evalúa al importar el módulo, cuando todavía no hay organización
activa, y el filtro implícito queda sin aplicar. Una vista nueva que no herede
de esa base expone los datos de todos los negocios.

**2. Todo cambio queda en la bitácora, sin escribir código para eso.**
Señales de Django llenan `bitacora` (quién, qué, cuándo, desde qué IP) y
`bitacora_detalle` (valor anterior y nuevo, campo por campo). Un cambio hecho
con `queryset.update()` **se salta las señales** y no queda auditado: usar
`save()` en todo lo que deba dejar rastro.

**3. Una nota de venta impresa apunta para siempre a su dominio.**
El QR codifica `https://<dominio>/nota/<token>/`. Si el dominio cambia, las
notas ya entregadas a los clientes quedan rotas. Antes de emitir notas reales
se fija el dominio definitivo en `NOTA_PUBLICA_BASE_URL`. El token es un UUID
aleatorio: la URL no se puede adivinar recorriendo números.

**4. Vender bajo el precio mínimo exige confirmarlo.**
La API responde **400** si una línea va por debajo de `precio_venta_minimo`, y
solo acepta el documento si vuelve con `autorizar_precio_bajo=true`. El
documento queda marcado `bajo_minimo` para revisar después quién negoció bajo
el piso. Aplica también a cotizaciones: cotizar bajo el mínimo es prometer
venderlo así.

**5. Lo público no expone costos.**
El escaparate (`/api/tienda/<slug>/`) y la nota QR no llevan login, a propósito:
el cliente final no tiene cuenta. Por eso sus serializadores son otros y nunca
incluyen precio de compra, mínimos ni stock.

---

## Estructura

```
backend/                Django (API REST + notas QR públicas)
  config/               settings, urls, wsgi
  apps/comun/           base multi-tenant: middleware, ViewSet base, pruebas base
  apps/cuentas/         usuarios, organizaciones, membresías y roles, login
  apps/auditoria/       bitácora y detalle por campo (llenadas por señales)
  apps/catalogo/        categorías, productos, historial de precios
  apps/terceros/        clientes, proveedores, transportadoras
  apps/ventas/          ventas, cotizaciones, listas, nota pública por QR
  apps/tienda/          escaparate público por slug
  Dockerfile            imagen de producción (contexto = raíz del repo)
frontend/               panel ERP — React + TypeScript (Vite)
  src/api/              el contrato con el backend (axios, tipos, recursos)
  src/auth/             sesión, organización activa, rol y permisos
  src/paginas/          una por sección del menú
index.html, service-worker.js, manifest.json
                        PWA de listas (en la raíz porque la publica GitHub Pages)
docs/                   plan vivo, despliegue y traspasos entre sesiones
compose.yml             entorno local: PostgreSQL 17 + API
```

### Dónde mirar antes de escribir código

| Si vas a… | Lee primero |
|---|---|
| **levantar el entorno por primera vez** | **[Arranque rápido](#arranque-rápido)**, arriba |
| **retomar después de un tiempo** | **[docs/SIGUIENTE-SESION.md](docs/SIGUIENTE-SESION.md)** — qué quedó hecho, qué falta y qué se decidió |
| **desplegar o tocar variables de producción** | **[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md)** — Railway + Supabase, y las trampas conocidas |
| entender por qué algo es como es | [docs/PLAN.md](docs/PLAN.md) §3 — las decisiones, una por una |
| tocar el modelo de datos | [docs/PLAN.md](docs/PLAN.md) §5 |
| configurar tu `.env` | [backend/.env.example](backend/.env.example) — cada variable explicada, y cuáles lee el código |
| escribir código del panel | [frontend/README.md](frontend/README.md) |
| levantar el backend sin Docker | [backend/README.md](backend/README.md) |
| ver cómo se construyó la Fase 3 | [docs/FASE3-PENDIENTE.md](docs/FASE3-PENDIENTE.md) |

---

## Cómo contribuir

`main` es la rama que despliega Railway: lo que entra ahí sale a producción.

Commits en español, con la convención `tipo(alcance): descripción`:

```
feat(ventas): aplicar ofertas 2x1 al armar la venta
fix(nota-qr): usar NOTA_PUBLICA_BASE_URL también en el SVG
chore(docker): fijar postgres 17 en el compose
```

Tipos: `feat` · `fix` · `docs` · `chore` · `test` · `refactor`.

Antes de subir: `docker compose exec api python manage.py test` en verde y
`npm run build` sin errores en `frontend/`.

## Autor

**Luis Mateo Hurtado Castro** — Ingeniería en Sistemas · [@MatiusProg](https://github.com/MatiusProg)

## Licencia

Todos los derechos reservados. El código es visible, pero no se concede permiso
de uso, copia ni redistribución.

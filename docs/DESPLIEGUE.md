# Despliegue: Supabase (base de datos) + Railway (API)

> **Estado al 2026-10-06: desplegado.**
> API: <https://api-production-6462.up.railway.app>.
> Las decisiones de costo y seguridad que explican esta configuración están en
> [PLAN.md](PLAN.md), decisiones 11 y 12.

| Pieza | Dónde vive | Cómo se publica |
|---|---|---|
| Base de datos | **Supabase**: proyecto `kinemart`, org *ArmonIA*, `us-east-1` | migraciones automáticas en cada despliegue |
| API + admin + **notas por QR** | **Railway**: proyecto `sistema-erp`, servicio `api`, US East | cada push a `main` que toque `backend/` |
| Panel ERP (React) | **Cloudflare Workers** (archivos estáticos): `kinemart` | cada push a `main` (build en Cloudflare) |
| PWA de listas | GitHub Pages | push a `main` |

> El QR de la nota apunta a la API (`/nota/<token>/`), así que **Railway es
> quien sirve las notas al cliente final**. Antes de emitir ventas reales hay que
> fijar el dominio definitivo: los QR ya impresos siguen apuntando al dominio con
> el que se emitieron.

---

## 1. Supabase: la base de datos

**Región:** *East US (North Virginia)*, la misma zona que el "US East" de
Railway (unos 1–2 ms por consulta). Ohio agrega unos 10–15 ms, y una pantalla
hace decenas de consultas.

**Conexión:** botón **Connect → Direct → Session pooler** (puerto **5432**):

```
postgresql://postgres.<REF>:<CLAVE>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

- **No usar "Direct connection".** Es solo IPv6.
- **No usar "Transaction pooler" (6543).** Rompe las sentencias preparadas de
  Django. `settings.py` igual detecta el 6543 y las desactiva, pero no hace falta
  pasar por eso.
- La cadena completa vive en `backend/.env` como `SUPABASE_DB_URL`, que el
  código no lee, y en Railway como `DATABASE_URL`.

**Data API apagada** (*Integrations → Data API*). Sin RLS, expondría las tablas
por REST. **No volver a prenderla sin RLS** (PLAN.md, decisión 12).

**Probar contra Supabase desde tu PC**, con la misma imagen que corre en
Railway:

```bash
export DATABASE_URL="$(grep '^SUPABASE_DB_URL=' backend/.env | cut -d= -f2-)"
docker compose run --rm --no-deps -e DATABASE_URL api python manage.py migrate
```

---

## 2. Railway: la API

**La configuración vive en el panel de Railway**, no en el repo. Desde el
2026-08-28 los servicios nuevos ya no pueden usar `railway.json` (Config as
Code); este servicio lo ignoraba y por eso se borró. El reemplazo es
Infrastructure as Code (`.railway/railway.ts`), pero hoy su referencia no
documenta serverless ni watch paths. Se adopta cuando lo haga (§ pendientes).

| Ajuste (Settings) | Valor | Por qué |
|---|---|---|
| Source → **Wait for CI** | activado | solo despliega si GitHub Actions pasó en verde |
| Build → Builder | **Dockerfile**, `/backend/Dockerfile` | la misma imagen que en local y en el CI |
| Build → Watch Paths | `/backend/**`, `/.dockerignore` | un cambio de docs o del panel no redespliega |
| Deploy → Pre-deploy | `python manage.py migrate --noinput` | si una migración falla, sigue la versión anterior |
| Deploy → Healthcheck | `/salud/` | 200 solo si la base responde; exenta de la redirección HTTPS (Railway la llama por HTTP con Host `healthcheck.railway.app`) |
| Deploy → **Serverless** | activado | se duerme tras 10 min sin tráfico: no paga RAM ociosa |
| Scale → Región | US East (Virginia), `us-east4-eqdc4a` | junto a Supabase. **Railway crea en Ámsterdam por defecto** |
| Scale → Memoria | tope de 1 GB | si algo se descontrola, no se come el presupuesto |
| Workspace → Usage | límite duro $10 (mínimo posible), aviso en $5 | Railway apaga en vez de cobrar |

**Serverless y la base de datos:** para que el servicio pueda dormirse,
`DB_CONN_MAX_AGE=0`. Una conexión persistente a Supabase cuenta como tráfico
saliente, y con ella abierta el servicio no se dormía (medido el 2026-10-06).

**Cuánto cuesta despertarlo** (medido el 2026-10-06, desde Bolivia): la primera
petición tras 10+ min sin uso tarda **~1.85 s**; las siguientes, ~0.5 s. Si
algún día molesta, apagar Serverless cuesta unos $2–2.5/mes de RAM (2 workers).

### Variables

| Variable | Valor |
|---|---|
| `DATABASE_URL` | Session pooler de Supabase (cargada por stdin, nunca en un comando) |
| `DJANGO_SECRET_KEY` | aleatoria, **distinta a la local**. Solo existe en Railway |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `localhost` (el dominio de Railway lo agrega `settings.py` desde `RAILWAY_PUBLIC_DOMAIN`) |
| `CORS_ALLOWED_ORIGINS` | `https://matiusprog.github.io`, `https://kinemart.luismateo-hurtado.workers.dev` + `localhost:5173` (panel local contra prod) |
| `CSRF_TRUSTED_ORIGINS` | `https://matiusprog.github.io`, `https://kinemart.luismateo-hurtado.workers.dev` |
| `DJANGO_TIME_ZONE` | `America/La_Paz` |
| `WEB_CONCURRENCY` | `2` (workers de gunicorn) |
| `DB_CONN_MAX_AGE` | `0` (ver serverless, arriba) |

Para cargar un secreto sin que quede en el historial de la terminal:

```bash
python -c "import secrets;print(secrets.token_urlsafe(50),end='')" \
  | railway variable set DJANGO_SECRET_KEY --stdin --service api
```

### Comprobar que quedó bien

```bash
U=https://api-production-6462.up.railway.app
curl -s $U/salud/                                               # {"estado": "ok"}
curl -sI $U/admin/login/ | grep -i strict-transport             # HSTS presente
curl -s -o /dev/null -w "%{http_code}\n" http://${U#https://}/  # 301 → https
```

La prueba que importa: **emitir una venta y escanear el QR con un celular de
verdad**. Tiene que abrir la nota y dejar guardarla en la galería.

En producción hay una cuenta de prueba (`PROD_PRUEBA_*` en `backend/.env`) con
la organización **"PRUEBA DESPLIEGUE (borrar)"**. Hay que borrarla antes de
cargar datos reales.

---

## 3. Panel ERP (React): Cloudflare

**URL:** <https://kinemart.luismateo-hurtado.workers.dev> (provisional, hasta
tener el dominio de ArmonIA: `kinemart.<dominio>`).

- Cuenta de Cloudflare de Mateo. Worker `kinemart` conectado al repo por la app
  "Cloudflare Workers and Pages" de GitHub, que tiene acceso solo a los repos
  elegidos: `barberia-torrez` y `Software_ERP`.
- **Configuración en el repo:** [`frontend/wrangler.jsonc`](../frontend/wrangler.jsonc).
  Solo archivos estáticos, con `not_found_handling: "single-page-application"`
  para que recargar en `/ventas` no dé 404.
- **Configuración en el panel de Cloudflare:** ruta `/frontend`, build
  `npm ci && npm run build`, deploy `npx wrangler deploy`.
- **La URL de la API** sale de [`frontend/.env.production`](../frontend/.env.production)
  (`VITE_API_URL`). No es secreta, porque termina dentro del JS publicado.
- **Por qué Cloudflare y no un segundo servicio en Railway:** es gratis, sirve
  desde la CDN más cercana y nunca se duerme. La API sí se duerme; el panel
  aparece al instante.
- **Cada origen nuevo del panel** (otro dominio, una preview) va en
  `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` de Railway. Si no, el login
  falla con un error de red que no dice "CORS".

## 4. PWA de listas

Sigue en GitHub Pages. Al conectarse al negocio, en el modal se escribe la URL de
Railway. Hay que agregar el origen de Pages
(`https://matiusprog.github.io`, ya agregado) a `CORS_ALLOWED_ORIGINS`.

---

## Notas y trampas conocidas

- **`DEBUG=False` activa el endurecimiento** (redirección a HTTPS, HSTS, cookies
  seguras). Si algo deja de responder tras desplegar, revisar primero
  `ALLOWED_HOSTS`: un host que falta devuelve 400 sin explicación.
- **Build**: Railway construye `backend/Dockerfile` (configurado en el panel), la
  misma imagen que se prueba en local con `docker compose`. Lo que funciona en tu
  PC funciona allá.
- **Migraciones**: corren solas en cada despliegue (`preDeployCommand`). Si una
  falla, el despliegue se cancela y sigue sirviendo la versión anterior — es a
  propósito, para no servir con la base a medias.
- **No correr `datos_demo` en producción**: crea usuarios con la contraseña
  `clave12345`, que está publicada en este repo público.
- **El QR depende del dominio**: si más adelante se usa un dominio propio, hay
  que fijar `NOTA_PUBLICA_BASE_URL` con él para que las notas nuevas apunten ahí.
  Las ya emitidas seguirán llevando al dominio viejo, así que conviene mantener
  una redirección.
- **Un despliegue en SKIPPED no se retoma solo.** Con "Wait for CI", si el CI
  de un commit se cancela o falla, Railway lo marca SKIPPED. Aunque después se
  relance el CI y pase, hay que desplegar a mano:
  `railway redeploy --service api --from-source -y` (toma el último commit de
  `main`). `railway redeploy` sin `--from-source` repite el despliegue viejo.
- **"1/1 replicas never became healthy"** con el build en verde = el
  healthcheck no recibe 200. Las dos causas que ya pasaron: el Host
  `healthcheck.railway.app` fuera de `ALLOWED_HOSTS` (400) y la redirección a
  HTTPS (301). `/salud/` resuelve las dos.
- **Railway crea los servicios nuevos en Ámsterdam.** Revisar Scale → Región.

# Despliegue — Supabase (base de datos) + Railway (backend)

Cierre de la Fase 3. El código ya está listo para producción: solo faltan las
cuentas y pegar las variables de entorno.

Reparto de piezas:

| Pieza | Dónde vive | Cómo se publica |
|---|---|---|
| Base de datos | **Supabase** (Postgres administrado) | se crea el proyecto y se copia la cadena de conexión |
| API + admin + **notas por QR** | **Railway** | se conecta el repo de GitHub |
| Panel ERP (React) | Railway estático, Vercel o Netlify | `npm run build` → carpeta `dist/` |
| PWA de listas | GitHub Pages (como hoy) | se sube el repo |

> El QR de la nota apunta al backend (`/nota/<token>/`), así que **Railway es
> quien sirve las notas al cliente final**. Por eso el dominio de Railway tiene
> que ser el definitivo antes de emitir ventas reales: los QR ya impresos siguen
> apuntando a ese dominio.

---

## 1. Supabase — la base de datos

1. Crear un proyecto en [supabase.com](https://supabase.com). Guardar la
   contraseña de la base.

   **La región se elige para que coincida con la de Railway, no con Bolivia.**
   Railway no tiene servidores en Sudamérica, así que la app vivirá en EE.UU.;
   dejar la base en São Paulo haría que cada consulta cruzara el continente. Una
   pantalla del panel dispara decenas de consultas, así que eso se multiplica:
   ~120 ms por consulta contra ~1 ms si están juntas.

   Mirar qué ciudad dice la UI de Railway (US East suele ser *Virginia*) y elegir
   esa misma en Supabase — *East US (North Virginia)* u *Ohio* según corresponda.
   Acertar la costa ya resuelve casi todo; acertar la ciudad ahorra otros ~10 ms.
2. **Project Settings → Database → Connection string → URI**. Copiar la cadena:

   ```
   postgresql://postgres.[REF]:[CLAVE]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
   ```

   Usar la del **pooler** (puerto 6543): Railway abre y cierra conexiones y el
   pooler evita quedarse sin cupo.

   El pooler es PgBouncer en **modo transacción**, que no admite sentencias
   preparadas ni cursores del lado del servidor. `settings.py` detecta el puerto
   6543 y los desactiva solo. Si algún día se usa otro pooler en un puerto
   distinto, poner `DB_POOLER=True` para forzar el mismo ajuste. Saltarse esto no
   rompe el arranque: falla más tarde, con `prepared statement "..." already
   exists`, cuando una consulta ya se repitió varias veces.
3. Probar en local antes de desplegar (con el venv activo, dentro de `backend/`):

   ```bash
   DATABASE_URL="postgresql://..." python manage.py migrate
   DATABASE_URL="postgresql://..." python manage.py datos_demo
   ```

   Si `migrate` termina sin errores, la conexión está bien.

---

## 2. Railway — el backend

1. Crear cuenta en [railway.app](https://railway.app) → **New Project → Deploy
   from GitHub repo** → elegir este repositorio.
2. Railway lee `railway.json` de la raíz: instala `backend/requirements.txt`,
   corre `collectstatic`, aplica las migraciones y levanta gunicorn.
3. **Variables** (Settings → Variables):

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | la cadena del pooler de Supabase |
   | `DJANGO_SECRET_KEY` | una clave nueva de 50+ caracteres (ver abajo) |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | tu dominio de Railway |
   | `CORS_ALLOWED_ORIGINS` | URLs del panel y de la PWA, separadas por coma |
   | `CSRF_TRUSTED_ORIGINS` | las mismas, con `https://` |
   | `DJANGO_TIME_ZONE` | `America/La_Paz` |

   `RAILWAY_PUBLIC_DOMAIN` la pone Railway sola y el `settings.py` ya la añade a
   `ALLOWED_HOSTS` y a `CSRF_TRUSTED_ORIGINS`.

   Clave nueva:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
   ```

4. **Settings → Networking → Generate Domain** para obtener la URL pública.
5. Crear el primer usuario real:

   ```bash
   railway run python backend/manage.py createsuperuser
   ```

   O registrar el negocio desde el panel (botón «Registrar un negocio nuevo»).

### Comprobar que quedó bien

```bash
curl https://TU-APP.railway.app/api/tienda/tienda-demo/productos/   # catálogo público
curl -X POST https://TU-APP.railway.app/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@erp.test","password":"clave12345"}'
```

Luego emitir una venta desde el panel y **escanear el QR con el celular**: debe
abrir `https://TU-APP.railway.app/nota/<token>/` y dejar guardar la imagen.

---

## 3. Panel ERP (React)

```bash
cd frontend
VITE_API_URL=https://TU-APP.railway.app npm run build
```

Publicar `frontend/dist/` donde sea (Railway static, Vercel, Netlify). Después,
agregar esa URL a `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` en Railway.

## 4. PWA de listas

Sigue en GitHub Pages. Al conectarse al negocio, en el modal se escribe la URL de
Railway. Hay que agregar el origen de Pages
(`https://usuario.github.io`) a `CORS_ALLOWED_ORIGINS`.

---

## Notas y trampas conocidas

- **`DEBUG=False` activa el endurecimiento** (redirección a HTTPS, HSTS, cookies
  seguras). Si algo deja de responder tras desplegar, revisar primero
  `ALLOWED_HOSTS`: un host que falta devuelve 400 sin explicación.
- **Build**: Railway construye `backend/Dockerfile` (ver `railway.json`), la
  misma imagen que se prueba en local con `docker compose`. Lo que funciona en tu
  PC funciona allá.
- **Migraciones**: corren solas en cada despliegue (`preDeployCommand`). Si una
  falla, el despliegue se cancela y sigue sirviendo la versión anterior — es a
  propósito, para no servir con la base a medias.
- **`datos_demo` es idempotente**: se puede correr en producción para tener con
  qué probar, y borrar esos registros después desde el admin.
- **El QR depende del dominio**: si más adelante se usa un dominio propio, hay
  que fijar `NOTA_PUBLICA_BASE_URL` con él para que las notas nuevas apunten ahí.
  Las ya emitidas seguirán llevando al dominio viejo, así que conviene mantener
  una redirección.

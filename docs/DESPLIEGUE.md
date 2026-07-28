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

1. Crear un proyecto en [supabase.com](https://supabase.com) (región más cercana:
   *South America (São Paulo)*). Guardar la contraseña de la base.
2. **Project Settings → Database → Connection string → URI**. Copiar la cadena:

   ```
   postgresql://postgres.[REF]:[CLAVE]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
   ```

   Usar la del **pooler** (puerto 6543): Railway abre y cierra conexiones y el
   pooler evita quedarse sin cupo.
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
- **Migraciones**: corren solas en cada despliegue (`startCommand`). Si una falla,
  el contenedor no arranca — es a propósito, para no servir con la base a medias.
- **`datos_demo` es idempotente**: se puede correr en producción para tener con
  qué probar, y borrar esos registros después desde el admin.
- **El QR depende del dominio**: si más adelante se usa un dominio propio, hay
  que fijar `NOTA_PUBLICA_BASE_URL` con él para que las notas nuevas apunten ahí.
  Las ya emitidas seguirán llevando al dominio viejo, así que conviene mantener
  una redirección.

# Dónde retomar

> Actualizado el **2026-08-02**. La reunión con el cliente es el **lunes
> 2026-08-03** — mañana. Es **presentación, no venta real**: no se emitirán notas
> que el cliente se lleve escaneadas, y se seguirá puliendo antes de producción.

---

## 0. LO QUE FALTA AHORA MISMO (dos cuentas por crear)

El código está listo y subido. Lo único pendiente es lo que solo puede hacer el
usuario a mano:

1. ⬜ **Crear el proyecto en Supabase.** Elegir la región **que coincida con la de
   Railway** (ver `DESPLIEGUE.md` §1 — ya NO es São Paulo). Guardar la contraseña
   al crearlo, porque no se vuelve a mostrar. Copiar la cadena del **pooler
   (puerto 6543)**.
2. ⬜ **Probar la conexión antes de desplegar**, desde `backend/`:
   `DATABASE_URL="postgresql://..." python manage.py migrate`
3. ⬜ **Crear el proyecto en Railway** (*Deploy from GitHub repo* → `Software_ERP`),
   región US East. Pegar las variables de `DESPLIEGUE.md` §2.
4. ⬜ **Generar el dominio** y agregarlo junto al origen de la PWA a
   `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`.

Decidido: se usa **Railway** (el usuario ya lo conoce) sobre una **cuenta
provisional**, a migrar a la cuenta oficial más adelante. Migrar es barato —
Railway no guarda estado, la base está en Supabase y el código en GitHub — pero
**hay que migrar antes de emitir notas de venta reales**, porque el dominio no se
muda y los QR ya impresos apuntarían a la cuenta vieja.

Aviso para el lunes: si se despliega en Render en vez de Railway, recordar que el
servicio gratuito se duerme y tarda ~50 s en despertar; conviene abrir la URL unos
minutos antes de la reunión.

---

## 1. Lo que quedó terminado y probado

| Bloque | Estado |
|---|---|
| Backend Fase 3 (ventas, cotizaciones, listas, escaparate) | ✅ |
| **Nota de venta por QR** (guardar en galería · WhatsApp · PDF) | ✅ |
| **Panel ERP en React** (`frontend/`), tema claro/oscuro | ✅ |
| **PWA conectada** al ERP + precio unitario (`6x18`) | ✅ |
| **Precio mínimo con confirmación** al vender y cotizar | ✅ |
| Preparación del despliegue (`DATABASE_URL`, gunicorn, whitenoise) | ✅ |
| Arreglo del **pooler de Supabase** (PgBouncer modo transacción) | ✅ |
| **Desplegar en Supabase + Railway** | ⏳ falta crear las cuentas (§0) |

Se verificó que **la PWA no se rompe** con el sistema desplegado: la URL del
backend se escribe a mano en el modal de conexión (no está quemada), el service
worker deja pasar de largo todo lo que sea de otro origen, y los 4 endpoints que
usa (`/api/auth/token/`, `.../refresh/`, `/api/listas/`, `/api/cotizaciones/`)
existen. Lo único imprescindible: agregar el origen de GitHub Pages a
`CORS_ALLOWED_ORIGINS`, o la PWA no conecta y el error no dice «CORS» claramente.

**55 pruebas en verde.** Levantar todo:

```bash
source backend/.venv/Scripts/activate && cd backend
python manage.py runserver          # API + notas QR
cd ../frontend && npm run dev       # panel en :5173
```

Usuarios de prueba (los crea `python manage.py datos_demo`):
`demo@erp.test` / `clave12345` (propietario) · `vendedor@erp.test` / `clave12345`.

---

## 2. Lo primero al retomar: **desplegar**

Decidido: **se despliega primero** y recién después se construye el catálogo.

**Base de datos** (ya cerrado): Supabase free ahora; cuando entre el primer cliente
que paga, mover el Postgres a Railway cambiando `DATABASE_URL` — una variable, sin
tocar código ni migraciones.

Para arrancar hace falta que el usuario cree las cuentas (~30 min, es lo único que
no se puede adelantar):

1. Proyecto en **Supabase** → copiar la cadena de conexión del *pooler* (puerto 6543).
2. Cuenta en **Railway** → *Deploy from GitHub repo* sobre este repositorio.
3. Pegar las variables de entorno de la tabla de [`DESPLIEGUE.md`](DESPLIEGUE.md) §2.

El resto (migraciones, `collectstatic`, gunicorn, dominios, CORS/CSRF) ya está
resuelto en `railway.json` y en `settings.py`.

Al terminar, la prueba que importa: **emitir una venta y escanear el QR con un
celular de verdad** — que abra la nota y deje guardarla en la galería.

---

## 3. El catálogo: qué replicar de **el-mercadillo**

Se clonó y se leyó el esquema real (`supabase/migrations/`). No eran atributos
dinámicos por categoría ni listas de precios: la riqueza estaba en **el producto
y en las ofertas**. Esto es lo que tenía y nosotros no:

| En el-mercadillo | Qué hace | ¿Lo tenemos? |
|---|---|---|
| `image_url` | foto del producto | ❌ **falta** |
| `description` | texto largo | ❌ **falta** |
| `discount_price` | precio de oferta (se muestra el normal tachado) | ❌ **falta** |
| `bundle_quantity` + `bundle_price` | paquete: «3 por Bs 10» | ❌ **falta** |
| `out_of_stock` | marcar agotado a mano, aparte del stock | ❌ **falta** |
| `special_offers` | **2x1**, **combo** (2 productos a un precio), oferta suelta | ❌ **falta** |
| `is_service` + `service_description` | servicio sin precio fijo | ✅ (`es_servicio`) |
| `products_public` (vista sin `precio_costo`) | catálogo público sin costos | ✅ (app `tienda`) |
| `categories` | categorías planas | ✅ |

Ojo: **no había variantes** (color/talla) en el-mercadillo. El usuario sí las pidió,
así que ese diseño hay que inventarlo — y encaja mejor junto a la Fase 4 (inventario),
porque cada variante necesita su propio stock.

### ⚠️ El cliente pidió inventario, y eso cambia este plan

El **2026-07-30** el cliente manifestó interés explícito en inventario (la Fase 4)
con requisitos concretos:

- Tiene **2 sucursales** y hace **viajes departamentales** en los que se ausenta;
  el inventario manual le lleva cada vez más tiempo.
- **Lotes**, con **fecha de vencimiento** y **fecha de llegada**.
- **Atar lotes y productos a un proveedor**.
- **Código de barras**, para inventariar con un lector.
- Info extra del producto, relacionada con la PWA, incluyendo **historial**.

Esto es demanda validada por un cliente que paga, no especulación del roadmap. Y
choca con el punto 1 de la lista de abajo: **con dos sucursales, un booleano
`agotado` en `Producto` miente** — puede estar agotado en una y no en la otra. El
stock deja de ser un número en el producto y pasa a ser por almacén; con lotes, el
eje real es `(producto, almacén, lote)`. Las variantes que el usuario ya quería
caen sobre ese mismo eje, así que ahora encajan en vez de ser un diseño aparte.

Antes de escribir la migración del catálogo, revisar que esos campos no choquen
con stock por sucursal y por lote. `PLAN.md` Fase 4 hoy solo prevé `almacen` +
`movimiento_stock`: se queda corto y hay que ampliarlo con `lote`, `proveedor` y
las fechas.

Nota barata: **un lector de código de barras se comporta como un teclado** (teclea
los dígitos y manda Enter). No hay que integrar hardware — basta un campo
`codigo_barras` y cuidar el foco del input en el panel.

### Orden sugerido para el catálogo

1. **Campos del producto** — `descripcion`, `imagen_url`, `precio_oferta`,
   `paquete_cantidad` + `paquete_precio`, `agotado`. Migración + panel + escaparate.
   Es lo que más se ve por lo poco que cuesta.
2. **Ofertas especiales** — modelo `Oferta` (2x1 / combo / especial) con vigencia.
   Al armar la venta, el POS las detecta y las aplica.
3. **Fotos de verdad** — subida a Supabase Storage (1 GB gratis en el plan free).
   Redimensionar en el navegador antes de subir; guardar solo la URL.
4. **Escaparate con fotos** — página pública mirable, para mandar por WhatsApp.
   Ya existe la API (`/api/tienda/<slug>/productos/`); falta la cara.
5. **Variantes** — junto a la Fase 4, con su propio stock por variante.

### Volver a mirar el repo de referencia

Es privado (WebFetch da 404) pero git sí entra con las credenciales guardadas:

```bash
git clone --depth 1 https://github.com/MatiusProg/el-mercadillo
```

Lo que interesa está en `supabase/migrations/*.sql` (el esquema) y en `src/pages`
(cómo se veía). El clon anterior se borró porque su `.env` traía claves reales.

---

## 4. Detalles que quedaron anotados al pasar

- **El QR queda atado al dominio que lo emite.** Antes de vender de verdad, fijar el
  dominio definitivo: una nota ya impresa apunta para siempre a esa URL. Si se cambia,
  hay que dejar una redirección (`NOTA_PUBLICA_BASE_URL`).
- **Quién autoriza el precio bajo**: hoy cualquiera que pueda vender. Si se quiere que
  solo propietario/admin puedan, es una comprobación de rol en
  `_DocumentoConLineasMixin.validate` (`backend/apps/ventas/serializers.py`).
- **La moneda está fija en «Bs»** en tres lugares (panel, nota pública, PWA). Cuando
  haya un cliente fuera de Bolivia, toca un campo `moneda` en `Organizacion`.
- **El panel no se revisó en pantalla por nadie más que el usuario**: no hubo
  navegador disponible en la sesión. Si algo se ve raro, es lo primero a mirar.

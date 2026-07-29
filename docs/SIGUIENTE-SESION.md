# Dónde retomar

> Escrito al cerrar la sesión del **2026-07-27/29**. La reunión de venta con el
> cliente se movió al **lunes**, así que hay tiempo hasta entonces.

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
| **Desplegar en Supabase + Railway** | ⏳ |

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

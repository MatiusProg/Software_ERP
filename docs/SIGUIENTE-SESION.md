# Dónde retomar

> Actualizado el **2026-10-06**. El producto ahora se llama **Kinemart**
> (*Kinemart by ArmonIA*). El plan general de negocio está en
> `D:\TRABAJO\ArmonIA\ARMONIA-PLAN.md`.

---

## 0. Estado en una línea

**La API está desplegada y probada en producción**:
<https://api-production-6462.up.railway.app>
(Railway US East + Supabase `kinemart` us-east-1). Docker en local, CI en
GitHub Actions y despliegue con "Wait for CI". **56 pruebas en verde.**

---

## 1. Lo que se hizo el 2026-10-06

| Bloque | Estado |
|---|---|
| Docker: `backend/Dockerfile` multi-stage + `compose.yml` (Postgres 17 + API) | ✅ |
| CI: `.github/workflows/ci.yml` (pruebas en Docker, `check --deploy`, migraciones al día, oxlint + tsc + build) | ✅ |
| Supabase: proyecto `kinemart`, Session pooler 5432, migraciones aplicadas, **Data API apagada** | ✅ |
| Railway: servicio `api`, región US East, tope 1 GB, serverless, healthcheck `/salud/`, Wait for CI | ✅ |
| Límite duro de gasto en Railway: $10 (mínimo posible), aviso en $5 | ✅ |
| `Despliegue_plat_ecomerce` (Si2) pausado para ahorrar crédito | ✅ |
| `.env` reescrito y documentado (y el BOM que impedía leer la SECRET_KEY) | ✅ |
| README nuevo, decisiones 11 y 12 en PLAN.md, DESPLIEGUE.md al día | ✅ |

Medido: serverless sí duerme (con `DB_CONN_MAX_AGE=0`); despertar cuesta
~1.85 s en la primera petición, después ~0.5 s.

---

## 2. Pendiente inmediato (en orden)

1. ⬜ **Respaldo nocturno de Supabase** —
   `.github/workflows/respaldo-supabase.yml` está **escrito y probado en local
   pero SIN subir**: necesita dos secrets en GitHub (`SUPABASE_DB_URL` y
   `RESPALDO_FRASE`) y que Mateo guarde la frase fuera de GitHub. Subirlo sin
   los secrets haría fallar el workflow cada noche. Este mismo workflow es el
   que evita la pausa de 7 días del plan free.
2. ⬜ **Probar la nota QR con un celular de verdad.** Para que Claude la revise
   en Chrome, Mateo tiene que darle permiso a la extensión sobre
   `api-production-6462.up.railway.app`.
3. ⬜ **Publicar el panel React** y volverlo **PWA instalable** (el cliente usa
   iPhone; ver memoria `pwa-erp-iphone`). Hoy se usa en local contra la API de
   producción (`localhost:5173` está en CORS).
4. ⬜ **Borrar la organización de prueba** "PRUEBA DESPLIEGUE (borrar)" antes de
   cargar datos reales (credenciales en `backend/.env`, `PROD_PRUEBA_*`).
5. ⬜ **Planes por tenant + RLS** (decisiones 11 y 12 de PLAN.md), antes de la
   Fase 4. Con RLS listo se podría reactivar la Data API si hiciera falta.
6. ⬜ **Fase 4 — inventario** que pidió el cliente: stock por
   (producto, sucursal, lote), vencimientos, proveedores, código de barras.
   Ver §3.

Más adelante: dominio propio definitivo (antes de emitir notas reales, por el
QR), Infrastructure as Code de Railway cuando documente serverless, webhooks
por tenant, fotos en Supabase Storage (S3).

---

## 3. Catálogo e inventario: lo que pidió el cliente

El **2026-07-30** el cliente (el hermano de Karen) pidió inventario:

- **2 sucursales** y viajes departamentales; el inventario manual le pesa.
- **Lotes**, con **fecha de vencimiento** y **de llegada**.
- **Lotes y productos atados a un proveedor**.
- **Código de barras** para inventariar con lector (un lector se comporta como
  teclado: basta un campo `codigo_barras` y cuidar el foco del input).
- Info extra del producto relacionada con la PWA, con **historial**.

Con dos sucursales, un booleano `agotado` en `Producto` miente: el stock pasa a
ser por `(producto, almacén, lote)`. Las variantes (color/talla) caen sobre ese
mismo eje. `PLAN.md` Fase 4 hay que ampliarlo con `lote`, `proveedor` y fechas.

Del repo de referencia **el-mercadillo** falta replicar: `imagen_url`,
`descripcion`, `precio_oferta`, paquetes ("3 por Bs 10"), ofertas especiales
(2x1, combo). Se clona con
`git clone --depth 1 https://github.com/MatiusProg/el-mercadillo` (privado; su
`.env` trae claves reales: borrar el clon al terminar).

---

## 4. Detalles anotados al pasar

- **El QR queda atado al dominio que lo emite.** Fijar el dominio definitivo
  (`NOTA_PUBLICA_BASE_URL`) antes de vender de verdad.
- **Quién autoriza el precio bajo**: hoy cualquiera que pueda vender. Para
  limitarlo a propietario/admin: `_DocumentoConLineasMixin.validate`
  (`backend/apps/ventas/serializers.py`).
- **La moneda está fija en «Bs»** en panel, nota pública y PWA.
- **El refresco del token JWT no tiene prueba** (SimpleJWT declara soporte hasta
  Django 5.2 y aquí corre sobre 6.0).
- `backend/.venv` está roto (apuntaba a un Python 3.14 desinstalado); con
  Docker no hace falta.

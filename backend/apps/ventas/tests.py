from apps.comun.pruebas import BaseTenantAPITest
from apps.auditoria.models import Bitacora


class VentaAPITest(BaseTenantAPITest):
    def _crear_venta(self, **extra):
        data = {
            "cliente_nombre": "Mostrador",
            "detalles": [
                {"descripcion": "Coca 2L", "total": "113.00", "impuesto": "13.00"},
            ],
        }
        data.update(extra)
        return self.client.post("/api/ventas/", data, format="json")

    def test_crear_venta_calcula_totales_iva_incluido(self):
        self.auth("prop@a.test")
        r = self._crear_venta()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero"], "V-0001")
        self.assertEqual(r.data["total"], "113.00")
        self.assertEqual(r.data["impuesto_total"], "13.00")   # 113 × 13/113
        self.assertEqual(r.data["subtotal"], "100.00")
        self.assertEqual(r.data["detalles"][0]["impuesto_monto"], "13.00")

    def test_modo_unitario_calcula_total(self):
        self.auth("prop@a.test")
        r = self._crear_venta(detalles=[
            {"descripcion": "Aceite", "cantidad": "15", "precio_unitario": "20.00", "impuesto": "0"},
        ])
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["total"], "300.00")           # 15 × 20
        self.assertEqual(r.data["impuesto_total"], "0.00")
        self.assertEqual(r.data["detalles"][0]["total"], "300.00")

    def test_correlativo_por_organizacion(self):
        self.auth("prop@a.test")
        self.assertEqual(self._crear_venta().data["numero"], "V-0001")
        self.assertEqual(self._crear_venta().data["numero"], "V-0002")
        self.auth("prop@b.test")
        self.assertEqual(self._crear_venta().data["numero"], "V-0001")

    def test_vendedor_puede_vender(self):
        self.auth("vend@a.test")
        r = self._crear_venta()
        self.assertEqual(r.status_code, 201, r.data)

    def test_vendedor_no_puede_borrar_venta(self):
        self.auth("prop@a.test")
        vid = self._crear_venta().data["id"]
        self.auth("vend@a.test")
        r = self.client.delete(f"/api/ventas/{vid}/")
        self.assertEqual(r.status_code, 403)

    def test_admin_puede_borrar_venta(self):
        self.auth("prop@a.test")
        vid = self._crear_venta().data["id"]
        r = self.client.delete(f"/api/ventas/{vid}/")
        self.assertEqual(r.status_code, 204)

    def test_aislamiento_entre_tenants(self):
        self.auth("prop@a.test")
        self._crear_venta()
        self.auth("prop@b.test")
        r = self.client.get("/api/ventas/")
        self.assertEqual(r.data["count"], 0)

    def test_editar_reemplaza_lineas_y_recalcula(self):
        self.auth("prop@a.test")
        vid = self._crear_venta().data["id"]
        r = self.client.patch(f"/api/ventas/{vid}/", {"detalles": [
            {"descripcion": "A", "total": "113.00", "impuesto": "13.00"},
            {"descripcion": "B", "total": "113.00", "impuesto": "13.00"},
        ]}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(len(r.data["detalles"]), 2)
        self.assertEqual(r.data["total"], "226.00")

    def test_editar_venta_queda_auditada(self):
        self.auth("prop@a.test")
        vid = self._crear_venta().data["id"]
        self.client.patch(f"/api/ventas/{vid}/", {"estado_pago": "pagado"}, format="json")
        auditorias = Bitacora.objects.filter(
            modelo="ventas.Venta", objeto_id=str(vid), accion="actualizar"
        )
        self.assertTrue(auditorias.exists())

    def test_linea_sin_descripcion_ni_producto_rechazada(self):
        self.auth("prop@a.test")
        r = self._crear_venta(detalles=[{"total": "10.00"}])
        self.assertEqual(r.status_code, 400)

    def test_anonimo_rechazado(self):
        r = self.client.get("/api/ventas/")
        self.assertEqual(r.status_code, 401)


class CotizacionAPITest(BaseTenantAPITest):
    DATOS = {
        "cliente_nombre": "Cliente Uno",
        "detalles": [
            {"descripcion": "Servicio X", "total": "226.00", "impuesto": "13.00"},
        ],
    }

    def test_crear_cotizacion_numero_y_totales(self):
        self.auth("prop@a.test")
        r = self.client.post("/api/cotizaciones/", self.DATOS, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero"], "COT-0001")
        self.assertEqual(r.data["total"], "226.00")
        self.assertEqual(r.data["impuesto_total"], "26.00")

    def test_convertir_en_venta(self):
        self.auth("prop@a.test")
        cid = self.client.post("/api/cotizaciones/", self.DATOS, format="json").data["id"]
        r = self.client.post(f"/api/cotizaciones/{cid}/convertir_en_venta/")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["numero"], "V-0001")
        self.assertEqual(r.data["cotizacion_origen"], cid)
        self.assertEqual(r.data["total"], "226.00")
        # La cotización queda marcada como aceptada.
        cot = self.client.get(f"/api/cotizaciones/{cid}/")
        self.assertEqual(cot.data["estado"], "aceptada")


class ListaAPITest(BaseTenantAPITest):
    DATOS = {
        "titulo": "VENTA · MAMÁ DE KAREN",
        "items": [
            {"descripcion": "Oreo", "detalle": "(2)", "total": "31.00", "comprado": True},
            {"descripcion": "Chicle", "detalle": "(1/4)", "total": "35.00"},
        ],
    }

    def test_crear_lista_suma_total_sin_impuesto(self):
        self.auth("prop@a.test")
        r = self.client.post("/api/listas/", self.DATOS, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["total"], "66.00")
        self.assertEqual(len(r.data["items"]), 2)
        comprados = [i for i in r.data["items"] if i["comprado"]]
        self.assertEqual(len(comprados), 1)

    def test_vendedor_puede_crear_lista(self):
        self.auth("vend@a.test")
        r = self.client.post("/api/listas/", self.DATOS, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_aislamiento_entre_tenants(self):
        self.auth("prop@a.test")
        self.client.post("/api/listas/", self.DATOS, format="json")
        self.auth("prop@b.test")
        r = self.client.get("/api/listas/")
        self.assertEqual(r.data["count"], 0)

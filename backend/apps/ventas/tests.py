from decimal import Decimal

from apps.comun.pruebas import BaseTenantAPITest
from apps.auditoria.models import Bitacora
from apps.catalogo.models import Producto


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


class PrecioMinimoTest(BaseTenantAPITest):
    """El piso de precio del producto se respeta al vender y al cotizar.

    Vender bajo el mínimo no está prohibido —a veces se negocia— pero no puede
    pasar por descuido: la API lo rechaza y solo lo acepta con una confirmación
    explícita, que además queda marcada en el documento.
    """

    def setUp(self):
        super().setUp()
        self.auth("prop@a.test")
        self.producto = Producto.objects.create(
            organizacion=self.org, sku="P-1", nombre="Coca 2L",
            precio_venta=Decimal("18.00"), precio_venta_minimo=Decimal("16.00"),
            precio_compra=Decimal("13.00"), precio_compra_maximo=Decimal("15.00"),
            impuesto=Decimal("13"),
        )

    def _vender(self, linea, **extra):
        datos = {"cliente_nombre": "Mostrador", "detalles": [linea]}
        datos.update(extra)
        return self.client.post("/api/ventas/", datos, format="json")

    def test_precio_unitario_bajo_el_minimo_se_rechaza(self):
        r = self._vender({
            "producto": self.producto.id, "cantidad": "2",
            "precio_unitario": "15.00", "impuesto": "13",
        })
        self.assertEqual(r.status_code, 400)
        self.assertIn("precio_bajo_minimo", r.data)
        self.assertIn("16.00", r.data["precio_bajo_minimo"][0])

    def test_se_acepta_con_autorizacion_y_queda_marcada(self):
        r = self._vender(
            {"producto": self.producto.id, "cantidad": "2",
             "precio_unitario": "15.00", "impuesto": "13"},
            autorizar_precio_bajo=True,
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["bajo_minimo"])
        self.assertEqual(r.data["total"], "30.00")

    def test_venta_normal_no_queda_marcada(self):
        r = self._vender({
            "producto": self.producto.id, "cantidad": "2",
            "precio_unitario": "18.00", "impuesto": "13",
        })
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data["bajo_minimo"])

    def test_total_directo_tambien_se_controla(self):
        """Sin cantidad se asume 1 unidad, así que un total de 12 es bajo el piso."""
        r = self._vender({"producto": self.producto.id, "total": "12.00", "impuesto": "13"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("precio_bajo_minimo", r.data)

    def test_total_directo_de_varias_unidades_no_da_falso_aviso(self):
        """100 Bs pueden ser 6 unidades a 16.67: no hay motivo para frenar."""
        r = self._vender({"producto": self.producto.id, "total": "100.00", "impuesto": "13"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data["bajo_minimo"])

    def test_linea_libre_sin_producto_no_se_controla(self):
        r = self._vender({"descripcion": "Algo suelto", "total": "1.00", "impuesto": "13"})
        self.assertEqual(r.status_code, 201, r.data)

    def test_editar_una_venta_tambien_se_controla(self):
        vid = self._vender({
            "producto": self.producto.id, "cantidad": "1",
            "precio_unitario": "18.00", "impuesto": "13",
        }).data["id"]
        r = self.client.patch(f"/api/ventas/{vid}/", {"detalles": [
            {"producto": self.producto.id, "cantidad": "1",
             "precio_unitario": "10.00", "impuesto": "13"},
        ]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("precio_bajo_minimo", r.data)

    def test_cotizacion_tambien_respeta_el_minimo(self):
        datos = {"cliente_nombre": "Cliente", "detalles": [
            {"producto": self.producto.id, "cantidad": "1",
             "precio_unitario": "14.00", "impuesto": "13"},
        ]}
        r = self.client.post("/api/cotizaciones/", datos, format="json")
        self.assertEqual(r.status_code, 400)

        datos["autorizar_precio_bajo"] = True
        r = self.client.post("/api/cotizaciones/", datos, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["bajo_minimo"])

        # Al convertirla en venta, la venta hereda la marca sin volver a preguntar.
        venta = self.client.post(f"/api/cotizaciones/{r.data['id']}/convertir_en_venta/")
        self.assertEqual(venta.status_code, 201, venta.data)
        self.assertTrue(venta.data["bajo_minimo"])

    def test_se_pueden_listar_las_ventas_bajo_minimo(self):
        self._vender(
            {"producto": self.producto.id, "cantidad": "1",
             "precio_unitario": "15.00", "impuesto": "13"},
            autorizar_precio_bajo=True,
        )
        self._vender({"producto": self.producto.id, "cantidad": "1",
                      "precio_unitario": "18.00", "impuesto": "13"})
        r = self.client.get("/api/ventas/?bajo_minimo=true")
        self.assertEqual(r.data["count"], 1)


class NotaPublicaQRTest(BaseTenantAPITest):
    """La nota pública por QR: la abre el cliente, sin login y sin filtrarse nada
    de la organización más allá de su propia nota."""

    def _venta(self):
        self.auth("prop@a.test")
        r = self.client.post("/api/ventas/", {
            "cliente_nombre": "Doña Rosa",
            "detalles": [
                {"descripcion": "Coca 2L", "detalle": "1 java",
                 "cantidad": "6", "precio_unitario": "18.00", "impuesto": "13.00"},
            ],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        return r.data

    def _anonimo(self):
        self.client.credentials()   # quita el Bearer: a partir de aquí es un cliente cualquiera

    def test_venta_expone_token_y_links(self):
        venta = self._venta()
        self.assertTrue(venta["token_publico"])
        self.assertIn(f"/nota/{venta['token_publico']}/", venta["url_publica"])
        self.assertTrue(venta["url_qr"].endswith("/qr.svg"))

    def test_pagina_publica_abre_sin_login(self):
        venta = self._venta()
        self._anonimo()
        r = self.client.get(f"/nota/{venta['token_publico']}/")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.content.decode()
        self.assertIn("V-0001", cuerpo)
        self.assertIn("Org A", cuerpo)
        self.assertIn("Doña Rosa", cuerpo)
        self.assertIn("108.00", cuerpo)          # 6 × 18
        self.assertIn("Guardar imagen", cuerpo)  # las acciones para el cliente

    def test_json_publico_solo_trae_lo_del_cliente(self):
        venta = self._venta()
        self._anonimo()
        r = self.client.get(f"/api/nota/{venta['token_publico']}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["numero"], "V-0001")
        self.assertEqual(r.data["negocio"], "Org A")
        self.assertEqual(r.data["total"], "108.00")
        self.assertEqual(r.data["detalles"][0]["descripcion"], "Coca 2L")
        # Nada interno: ni ids, ni el token, ni datos de costo.
        for campo in ("id", "token_publico", "cliente", "organizacion", "cotizacion_origen"):
            self.assertNotIn(campo, r.data)

    def test_qr_svg_publico(self):
        venta = self._venta()
        self._anonimo()
        r = self.client.get(f"/nota/{venta['token_publico']}/qr.svg")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", r.content)

    def test_token_inexistente_es_404(self):
        self._anonimo()
        falso = "00000000-0000-4000-8000-000000000000"
        self.assertEqual(self.client.get(f"/nota/{falso}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/nota/{falso}/").status_code, 404)

    def test_cada_venta_tiene_su_propio_token(self):
        primera = self._venta()
        segunda = self._venta()
        self.assertNotEqual(primera["token_publico"], segunda["token_publico"])


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

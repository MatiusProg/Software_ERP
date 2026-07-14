from apps.comun.pruebas import BaseTenantAPITest


class CategoriaAPITest(BaseTenantAPITest):
    def test_nombre_unico_por_org_devuelve_400(self):
        self.auth("prop@a.test")
        self.client.post("/api/categorias/", {"nombre": "Bebidas"}, format="json")
        r = self.client.post("/api/categorias/", {"nombre": "Bebidas"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("nombre", r.data)

    def test_mismo_nombre_permitido_en_otra_org(self):
        self.auth("prop@a.test")
        self.client.post("/api/categorias/", {"nombre": "Bebidas"}, format="json")
        self.auth("prop@b.test")
        r = self.client.post("/api/categorias/", {"nombre": "Bebidas"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)


class ProductoAPITest(BaseTenantAPITest):
    def _crear_producto(self, **extra):
        data = {
            "sku": "P001", "nombre": "Coca 2L",
            "precio_venta": "12.00", "precio_venta_minimo": "10.00",
            "precio_compra": "9.00",
        }
        data.update(extra)
        return self.client.post("/api/productos/", data, format="json")

    def test_admin_crea_producto(self):
        self.auth("prop@a.test")
        r = self._crear_producto()
        self.assertEqual(r.status_code, 201, r.data)

    def test_vendedor_no_puede_crear_producto(self):
        self.auth("vend@a.test")
        r = self._crear_producto()
        self.assertEqual(r.status_code, 403)

    def test_vendedor_ve_precio_minimo(self):
        self.auth("prop@a.test")
        self._crear_producto()
        self.auth("vend@a.test")
        r = self.client.get("/api/productos/")
        self.assertEqual(r.status_code, 200)
        item = r.data["results"][0]
        self.assertEqual(item["precio_venta_minimo"], "10.00")

    def test_rechaza_minimo_mayor_que_venta(self):
        self.auth("prop@a.test")
        r = self._crear_producto(precio_venta="10.00", precio_venta_minimo="15.00")
        self.assertEqual(r.status_code, 400)
        self.assertIn("precio_venta_minimo", r.data)

    def test_historial_se_llena_al_cambiar_precio(self):
        self.auth("prop@a.test")
        pid = self._crear_producto().data["id"]
        self.client.patch(f"/api/productos/{pid}/", {"precio_venta": "13.50"}, format="json")
        r = self.client.get(f"/api/productos/{pid}/historial_precios/")
        ventas = [h for h in r.data["results"] if h["tipo"] == "venta"]
        self.assertEqual(len(ventas), 2)  # precio inicial + el cambio

    def test_sku_unico_por_organizacion(self):
        self.auth("prop@a.test")
        self._crear_producto()
        r = self._crear_producto()  # mismo sku en la misma org
        self.assertEqual(r.status_code, 400)

    def test_mismo_sku_permitido_en_otra_organizacion(self):
        self.auth("prop@a.test")
        self._crear_producto()
        self.auth("prop@b.test")
        r = self._crear_producto()
        self.assertEqual(r.status_code, 201, r.data)

    def test_aislamiento_entre_tenants(self):
        self.auth("prop@a.test")
        self._crear_producto()
        self.auth("prop@b.test")
        r = self.client.get("/api/productos/")
        self.assertEqual(r.data["count"], 0)

    def test_anonimo_rechazado(self):
        r = self.client.get("/api/productos/")
        self.assertEqual(r.status_code, 401)

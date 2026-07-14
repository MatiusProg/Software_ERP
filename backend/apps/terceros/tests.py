from apps.comun.pruebas import BaseTenantAPITest

DATOS = {
    "nombre": "Distribuidora Sur",
    "nit_ci": "123456",
    "es_proveedor": True,
    "contactos": [
        {"tipo": "telefono", "valor": "77712345"},
        {"tipo": "whatsapp", "valor": "77712345"},
    ],
    "ubicaciones": [{"direccion": "Av. Siempre Viva 123", "ciudad": "Santa Cruz"}],
}


class TerceroAPITest(BaseTenantAPITest):
    def test_vendedor_puede_crear_tercero_con_anidados(self):
        self.auth("vend@a.test")
        r = self.client.post("/api/terceros/", DATOS, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(len(r.data["contactos"]), 2)
        self.assertEqual(len(r.data["ubicaciones"]), 1)

    def test_vendedor_no_puede_borrar_tercero(self):
        self.auth("prop@a.test")
        tid = self.client.post("/api/terceros/", DATOS, format="json").data["id"]
        self.auth("vend@a.test")
        r = self.client.delete(f"/api/terceros/{tid}/")
        self.assertEqual(r.status_code, 403)

    def test_admin_puede_borrar_tercero(self):
        self.auth("prop@a.test")
        tid = self.client.post("/api/terceros/", DATOS, format="json").data["id"]
        r = self.client.delete(f"/api/terceros/{tid}/")
        self.assertEqual(r.status_code, 204)

    def test_filtro_es_proveedor(self):
        self.auth("prop@a.test")
        self.client.post("/api/terceros/", DATOS, format="json")
        self.client.post("/api/terceros/", {"nombre": "Cliente Uno", "es_cliente": True}, format="json")
        r = self.client.get("/api/terceros/?es_proveedor=true")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["nombre"], "Distribuidora Sur")

    def test_actualizar_reemplaza_contactos(self):
        self.auth("prop@a.test")
        tid = self.client.post("/api/terceros/", DATOS, format="json").data["id"]
        r = self.client.patch(
            f"/api/terceros/{tid}/",
            {"contactos": [{"tipo": "email", "valor": "hola@sur.test"}]},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(len(r.data["contactos"]), 1)
        self.assertEqual(r.data["contactos"][0]["tipo"], "email")

    def test_aislamiento_entre_tenants(self):
        self.auth("prop@a.test")
        self.client.post("/api/terceros/", DATOS, format="json")
        self.auth("prop@b.test")
        r = self.client.get("/api/terceros/")
        self.assertEqual(r.data["count"], 0)

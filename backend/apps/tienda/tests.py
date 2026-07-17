from decimal import Decimal

from apps.comun.pruebas import BaseTenantAPITest
from apps.catalogo.models import Categoria, Producto


class TiendaPublicaTest(BaseTenantAPITest):
    def setUp(self):
        super().setUp()
        self.cat = Categoria.objects.create(organizacion=self.org, nombre="Bebidas")
        Producto.objects.create(
            organizacion=self.org, sku="P001", nombre="Coca 2L", categoria=self.cat,
            precio_venta=Decimal("12.00"), precio_compra=Decimal("9.00"),
            precio_venta_minimo=Decimal("10.00"), stock=Decimal("5"),
        )
        Producto.objects.create(
            organizacion=self.org, sku="P002", nombre="Inactivo",
            activo=False, precio_venta=Decimal("5.00"),
        )
        # Producto de OTRA organización: no debe aparecer en esta tienda.
        Producto.objects.create(
            organizacion=self.otra, sku="X1", nombre="Ajeno", precio_venta=Decimal("1.00"),
        )

    def test_lista_productos_publica_sin_login(self):
        r = self.client.get(f"/api/tienda/{self.org.slug}/productos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)  # solo el activo de esta org
        self.assertEqual(r.data["results"][0]["nombre"], "Coca 2L")

    def test_no_expone_precios_internos_ni_stock(self):
        r = self.client.get(f"/api/tienda/{self.org.slug}/productos/")
        item = r.data["results"][0]
        for prohibido in ("precio_compra", "precio_compra_maximo",
                          "precio_venta_minimo", "stock"):
            self.assertNotIn(prohibido, item)
        self.assertEqual(item["precio_venta"], "12.00")

    def test_info_del_negocio(self):
        r = self.client.get(f"/api/tienda/{self.org.slug}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["nombre"], "Org A")

    def test_categorias_publicas(self):
        r = self.client.get(f"/api/tienda/{self.org.slug}/categorias/")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["nombre"], "Bebidas")

    def test_filtro_por_categoria(self):
        r = self.client.get(f"/api/tienda/{self.org.slug}/productos/?categoria={self.cat.id}")
        self.assertEqual(r.data["count"], 1)

    def test_slug_inexistente_404(self):
        r = self.client.get("/api/tienda/no-existe/productos/")
        self.assertEqual(r.status_code, 404)

    def test_organizacion_inactiva_404(self):
        self.org.activa = False
        self.org.save(update_fields=["activa"])
        r = self.client.get(f"/api/tienda/{self.org.slug}/productos/")
        self.assertEqual(r.status_code, 404)

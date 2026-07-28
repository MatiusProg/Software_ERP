"""
Datos de demostración para probar el sistema completo sin cargar nada a mano.

    python manage.py datos_demo

Es **idempotente**: se puede correr las veces que haga falta (usa get_or_create),
así que sirve tanto para la base local como para estrenar la de producción.
Crea una organización con dos usuarios (propietario y vendedor), catálogo,
clientes, ventas —cada una con su QR—, una cotización y una lista.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogo.models import Categoria, Producto
from apps.comun.tenancy import set_organizacion_actual
from apps.cuentas.models import Membresia, Organizacion, Usuario
from apps.terceros.models import ContactoTercero, Tercero
from apps.ventas.models import (
    Cotizacion, CotizacionDetalle, Lista, ListaItem,
    Venta, VentaDetalle, siguiente_numero,
)

CLAVE = "clave12345"

CATEGORIAS = ["Bebidas", "Abarrotes", "Limpieza", "Servicios"]

# (sku, nombre, categoría, precio_venta, mínimo, compra, máximo, stock, servicio)
PRODUCTOS = [
    ("BEB-001", "Coca Cola 2L", "Bebidas", "18.00", "16.00", "13.50", "15.00", "48", False),
    ("BEB-002", "Agua Vital 2L", "Bebidas", "8.00", "7.00", "5.50", "6.50", "60", False),
    ("BEB-003", "Cerveza Paceña 620ml", "Bebidas", "15.00", "13.00", "11.00", "12.50", "72", False),
    ("ABA-001", "Arroz Grano de Oro 1kg", "Abarrotes", "12.00", "11.00", "9.00", "10.00", "40", False),
    ("ABA-002", "Aceite Fino 900ml", "Abarrotes", "14.50", "13.50", "11.50", "12.50", "36", False),
    ("ABA-003", "Azúcar Guabirá 1kg", "Abarrotes", "7.50", "7.00", "5.80", "6.50", "50", False),
    ("ABA-004", "Fideo Princesa 400g", "Abarrotes", "6.00", "5.50", "4.20", "5.00", "80", False),
    ("ABA-005", "Leche Pil 1L", "Abarrotes", "9.50", "9.00", "7.50", "8.20", "30", False),
    ("LIM-001", "Detergente Ola 1kg", "Limpieza", "22.00", "20.00", "17.00", "18.50", "25", False),
    ("LIM-002", "Lavandina Patito 1L", "Limpieza", "9.00", "8.00", "6.50", "7.20", "40", False),
    ("LIM-003", "Papel higiénico Elite x4", "Limpieza", "16.00", "14.50", "12.00", "13.50", "35", False),
    ("SER-001", "Delivery en la zona", "Servicios", "10.00", "10.00", "0.00", "0.00", "0", True),
]

CLIENTES = [
    ("Doña Rosa Mamani", "4821990", "71234567"),
    ("Pensión La Casona", "1023456019", "70011223"),
    ("Karen Vega", "", "68899001"),
]


class Command(BaseCommand):
    help = "Carga datos de demostración (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug", default="tienda-demo",
            help="Slug de la organización de demo (por defecto: tienda-demo).",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        org, creada = Organizacion.objects.get_or_create(
            slug=opciones["slug"], defaults={"nombre": "Tienda Demo"}
        )
        set_organizacion_actual(org)
        self.stdout.write(f"Organización: {org.nombre} ({org.slug}) {'[nueva]' if creada else ''}")

        propietario = self._usuario("demo@erp.test", "Luis Demo", org, Membresia.Rol.PROPIETARIO)
        self._usuario("vendedor@erp.test", "Vendedor Demo", org, Membresia.Rol.VENDEDOR)

        categorias = {
            nombre: Categoria.objects.get_or_create(organizacion=org, nombre=nombre)[0]
            for nombre in CATEGORIAS
        }

        productos = {}
        for sku, nombre, cat, venta, minimo, compra, maximo, stock, servicio in PRODUCTOS:
            productos[sku] = Producto.objects.get_or_create(
                organizacion=org, sku=sku,
                defaults=dict(
                    nombre=nombre, categoria=categorias[cat], unidad="unidad",
                    es_servicio=servicio, precio_venta=Decimal(venta),
                    precio_venta_minimo=Decimal(minimo), precio_compra=Decimal(compra),
                    precio_compra_maximo=Decimal(maximo), stock=Decimal(stock),
                    impuesto=Decimal("13"),
                ),
            )[0]

        clientes = []
        for nombre, nit, telefono in CLIENTES:
            cliente, nuevo = Tercero.objects.get_or_create(
                organizacion=org, nombre=nombre,
                defaults=dict(nit_ci=nit, es_cliente=True),
            )
            if nuevo and telefono:
                ContactoTercero.objects.create(
                    organizacion=org, tercero=cliente, tipo="whatsapp", valor=telefono
                )
            clientes.append(cliente)

        ventas = [
            self._venta(org, clientes[0], "pagado", [
                (productos["BEB-001"], "1 java", Decimal("6"), None),
                (productos["ABA-002"], "", Decimal("3"), None),
                (None, "bolsa grande", None, Decimal("45.00")),
            ]),
            self._venta(org, None, "pendiente", [
                (productos["ABA-001"], "", Decimal("2"), None),
                (productos["LIM-001"], "", Decimal("1"), None),
            ], nombre_libre="Mostrador"),
        ]

        self._cotizacion(org, clientes[1], [
            (productos["BEB-003"], "5 cajas", Decimal("60"), None),
            (productos["ABA-005"], "", Decimal("24"), None),
        ])

        self._lista(org, clientes[2], [
            ("Oreo", "(2)", Decimal("31.00"), True),
            ("Chicle", "(1/4)", Decimal("35.00"), False),
            ("Galleta agua", "1 paquete", Decimal("12.50"), False),
        ])

        self.stdout.write(self.style.SUCCESS("\nListo. Para entrar al panel:"))
        self.stdout.write(f"  propietario: {propietario.email} / {CLAVE}")
        self.stdout.write(f"  vendedor:    vendedor@erp.test / {CLAVE}")
        self.stdout.write(f"  escaparate:  /api/tienda/{org.slug}/productos/")
        for venta in ventas:
            self.stdout.write(f"  nota {venta.numero}: /nota/{venta.token_publico}/")

    # ------------------------------------------------------------------ #
    def _usuario(self, email, nombre, org, rol):
        usuario, nuevo = Usuario.objects.get_or_create(
            email=email, defaults={"nombre_completo": nombre}
        )
        if nuevo:
            usuario.set_password(CLAVE)
            usuario.save(update_fields=["password"])
        Membresia.objects.get_or_create(usuario=usuario, organizacion=org, defaults={"rol": rol})
        return usuario

    def _lineas(self, org, cabecera, modelo, campo_fk, lineas, fiscal=True):
        """Crea las líneas y devuelve (total, impuesto) del documento."""
        total = impuesto = Decimal("0")
        for i, (producto, detalle, cantidad, directo) in enumerate(lineas):
            linea = modelo(
                organizacion=org, **{campo_fk: cabecera},
                producto=producto,
                descripcion=producto.nombre if producto else "Producto suelto",
                detalle=detalle, cantidad=cantidad,
                precio_unitario=producto.precio_venta if (producto and cantidad) else None,
                total=directo or Decimal("0"), orden=i,
            )
            if fiscal:
                linea.impuesto = Decimal("13")
            linea.total = linea.calcular_total()
            linea.save()
            total += linea.calcular_total()
            if fiscal:
                impuesto += linea.impuesto_monto
        return total, impuesto

    def _venta(self, org, cliente, estado_pago, lineas, nombre_libre=""):
        existente = Venta.todos.filter(
            organizacion=org, cliente=cliente, cliente_nombre=nombre_libre
        ).first()
        if existente:
            return existente
        venta = Venta.objects.create(
            organizacion=org, numero=siguiente_numero(org, "venta", "V"),
            cliente=cliente, cliente_nombre=nombre_libre, estado_pago=estado_pago,
            notas="Gracias por su compra. Cambios hasta 7 días con esta nota.",
        )
        total, impuesto = self._lineas(org, venta, VentaDetalle, "venta", lineas)
        venta.subtotal, venta.impuesto_total, venta.total = total - impuesto, impuesto, total
        venta.save(update_fields=["subtotal", "impuesto_total", "total"])
        return venta

    def _cotizacion(self, org, cliente, lineas):
        if Cotizacion.todos.filter(organizacion=org, cliente=cliente).exists():
            return
        cot = Cotizacion.objects.create(
            organizacion=org, numero=siguiente_numero(org, "cotizacion", "COT"),
            cliente=cliente, estado=Cotizacion.Estado.ENVIADA, validez_dias=15,
        )
        total, impuesto = self._lineas(org, cot, CotizacionDetalle, "cotizacion", lineas)
        cot.subtotal, cot.impuesto_total, cot.total = total - impuesto, impuesto, total
        cot.save(update_fields=["subtotal", "impuesto_total", "total"])

    def _lista(self, org, cliente, items):
        if Lista.todos.filter(organizacion=org, cliente=cliente).exists():
            return
        lista = Lista.objects.create(
            organizacion=org, titulo="VENTA · MAMÁ DE KAREN", cliente=cliente
        )
        total = Decimal("0")
        for i, (descripcion, detalle, monto, comprado) in enumerate(items):
            item = ListaItem.objects.create(
                organizacion=org, lista=lista, descripcion=descripcion, detalle=detalle,
                total=monto, comprado=comprado, orden=i,
            )
            total += item.calcular_total()
        lista.total = total
        lista.save(update_fields=["total"])

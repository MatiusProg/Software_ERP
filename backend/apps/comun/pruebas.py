"""
Utilidades compartidas para las pruebas de la API multi-tenant.

``BaseTenantAPITest`` monta dos organizaciones con usuarios de distintos roles y
ofrece ``auth(email)`` para autenticarse por JWT (que es el punto donde se
resuelve el tenant activo). También limpia el thread-local entre pruebas.
"""

from django.test import override_settings
from rest_framework.test import APITestCase

from apps.cuentas.models import Membresia, Organizacion, Usuario
from apps.comun.tenancy import set_organizacion_actual, set_usuario_actual

PASSWORD = "clave12345"


# Hasher rápido: acelera create_user + login en las pruebas (no afecta a producción).
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BaseTenantAPITest(APITestCase):
    def crear_usuario(self, email, org, rol):
        usuario = Usuario.objects.create_user(email=email, password=PASSWORD)
        Membresia.objects.create(usuario=usuario, organizacion=org, rol=rol)
        return usuario

    def auth(self, email):
        """Autentica al cliente como ``email`` obteniendo un token JWT real."""
        resp = self.client.post(
            "/api/auth/token/", {"email": email, "password": PASSWORD}, format="json"
        )
        assert resp.status_code == 200, resp.data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def setUp(self):
        set_organizacion_actual(None)
        set_usuario_actual(None)
        self.org = Organizacion.objects.create(nombre="Org A", slug="org-a")
        self.otra = Organizacion.objects.create(nombre="Org B", slug="org-b")
        self.propietario = self.crear_usuario("prop@a.test", self.org, Membresia.Rol.PROPIETARIO)
        self.vendedor = self.crear_usuario("vend@a.test", self.org, Membresia.Rol.VENDEDOR)
        self.ajeno = self.crear_usuario("prop@b.test", self.otra, Membresia.Rol.PROPIETARIO)

    def tearDown(self):
        set_organizacion_actual(None)
        set_usuario_actual(None)

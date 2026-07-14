from apps.comun.vistas import TenantModelViewSet
from apps.cuentas.permisos import MiembroEscribeAdminBorra
from .models import Tercero
from .serializers import TerceroSerializer


class TerceroViewSet(TenantModelViewSet):
    # El vendedor puede crear/editar clientes (los registra al vender); borrar,
    # solo propietario/admin.
    permission_classes = [MiembroEscribeAdminBorra]
    queryset = Tercero.objects.prefetch_related("contactos", "ubicaciones").all()
    serializer_class = TerceroSerializer
    filterset_fields = ["es_cliente", "es_proveedor", "es_transportadora", "activo"]
    search_fields = ["nombre", "nit_ci"]
    ordering_fields = ["nombre", "creado_en"]

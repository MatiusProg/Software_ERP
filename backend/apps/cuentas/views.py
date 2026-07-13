from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Usuario
from .permisos import rol_actual
from .serializers import RegistroSerializer, UsuarioSerializer


class RegistroView(GenericAPIView):
    """Alta pública de un negocio + su usuario propietario."""

    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


class YoView(APIView):
    """Datos del usuario logueado, sus membresías, organización y rol activos."""

    def get(self, request):
        data = UsuarioSerializer(request.user).data
        org = getattr(request, "organizacion", None)
        data["organizacion_activa"] = str(org.id) if org else None
        data["rol_activo"] = rol_actual(request)
        return Response(data)


class LoginView(TokenObtainPairView):
    """Login JWT que además registra el evento en la bitácora."""

    def post(self, request, *args, **kwargs):
        from apps.auditoria.models import Bitacora
        from apps.auditoria.servicios import crear_bitacora

        email = request.data.get("email", "")
        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            crear_bitacora(Bitacora.Accion.LOGIN_FALLIDO, descripcion=f"email={email}")
            raise

        usuario = Usuario.objects.filter(email__iexact=email).first()
        crear_bitacora(Bitacora.Accion.LOGIN, usuario=usuario, descripcion=f"email={email}")
        return response

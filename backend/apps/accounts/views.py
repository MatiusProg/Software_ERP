from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(GenericAPIView):
    """Alta pública de un negocio + su usuario propietario."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """Datos del usuario logueado, sus membresías y la organización activa."""

    def get(self, request):
        data = UserSerializer(request.user).data
        org = getattr(request, "organization", None)
        data["active_organization"] = str(org.id) if org else None
        return Response(data)

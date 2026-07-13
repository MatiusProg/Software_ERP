from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import Membresia, Organizacion, Usuario


class OrganizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizacion
        fields = ["id", "nombre", "slug", "activa"]


class MembresiaSerializer(serializers.ModelSerializer):
    organizacion = OrganizacionSerializer(read_only=True)

    class Meta:
        model = Membresia
        fields = ["id", "organizacion", "rol"]


class UsuarioSerializer(serializers.ModelSerializer):
    membresias = MembresiaSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "email", "nombre_completo", "membresias"]


class RegistroSerializer(serializers.Serializer):
    """Alta de un nuevo negocio: crea el usuario, su organización y lo deja como
    propietario en una sola transacción."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    nombre_completo = serializers.CharField(required=False, allow_blank=True)
    nombre_organizacion = serializers.CharField()

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return value

    def _slug_unico(self, nombre):
        base = slugify(nombre) or "org"
        slug = base
        i = 2
        while Organizacion.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nombre_completo=validated_data.get("nombre_completo", ""),
        )
        org = Organizacion.objects.create(
            nombre=validated_data["nombre_organizacion"],
            slug=self._slug_unico(validated_data["nombre_organizacion"]),
        )
        Membresia.objects.create(
            organizacion=org, usuario=usuario, rol=Membresia.Rol.PROPIETARIO
        )
        return usuario

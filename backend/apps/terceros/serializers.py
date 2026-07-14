from django.db import transaction
from rest_framework import serializers

from .models import ContactoTercero, Tercero, UbicacionTercero


class ContactoTerceroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactoTercero
        fields = ["id", "tipo", "valor"]


class UbicacionTerceroSerializer(serializers.ModelSerializer):
    class Meta:
        model = UbicacionTercero
        fields = ["id", "direccion", "ciudad", "referencia", "lat", "lng"]


class TerceroSerializer(serializers.ModelSerializer):
    contactos = ContactoTerceroSerializer(many=True, required=False)
    ubicaciones = UbicacionTerceroSerializer(many=True, required=False)

    class Meta:
        model = Tercero
        fields = [
            "id", "nombre", "nit_ci",
            "es_cliente", "es_proveedor", "es_transportadora",
            "notas", "activo",
            "contactos", "ubicaciones",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]

    def _crear_hijos(self, tercero, contactos, ubicaciones):
        # La organización se hereda del tercero (los hijos son del mismo tenant).
        ContactoTercero.objects.bulk_create([
            ContactoTercero(tercero=tercero, organizacion=tercero.organizacion, **c)
            for c in contactos
        ])
        UbicacionTercero.objects.bulk_create([
            UbicacionTercero(tercero=tercero, organizacion=tercero.organizacion, **u)
            for u in ubicaciones
        ])

    @transaction.atomic
    def create(self, validated_data):
        contactos = validated_data.pop("contactos", [])
        ubicaciones = validated_data.pop("ubicaciones", [])
        tercero = Tercero.objects.create(**validated_data)
        self._crear_hijos(tercero, contactos, ubicaciones)
        return tercero

    @transaction.atomic
    def update(self, instance, validated_data):
        # Si vienen contactos/ubicaciones, reemplazan por completo a los previos.
        contactos = validated_data.pop("contactos", None)
        ubicaciones = validated_data.pop("ubicaciones", None)

        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.save()

        if contactos is not None:
            instance.contactos.all().delete()
            self._crear_hijos(instance, contactos, [])
        if ubicaciones is not None:
            instance.ubicaciones.all().delete()
            self._crear_hijos(instance, [], ubicaciones)
        return instance

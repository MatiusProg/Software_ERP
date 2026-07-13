from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import Membership, Organization, User


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "is_active"]


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "role"]


class UserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "memberships"]


class RegisterSerializer(serializers.Serializer):
    """Alta de un nuevo negocio: crea el usuario, su organización y lo deja
    como propietario (owner) en una sola transacción."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(required=False, allow_blank=True)
    organization_name = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return value

    def _unique_slug(self, name):
        base = slugify(name) or "org"
        slug = base
        i = 2
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
        )
        org = Organization.objects.create(
            name=validated_data["organization_name"],
            slug=self._unique_slug(validated_data["organization_name"]),
        )
        Membership.objects.create(
            organization=org, user=user, role=Membership.Role.OWNER
        )
        return user

from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Client, Profile

User = get_user_model()


class ClientUserCreateSerializer(UserCreateSerializer):
    # сделаем email обязательным (иначе Client.email не заполнить)
    email = serializers.EmailField(required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ("id", "username", "password", "email")

    def create(self, validated_data):
        user = super().create(validated_data)

        username = user.username or ""
        email = user.email or validated_data.get("email")

        # минимально заполняем Client (потом клиент может отредактировать профиль)
        client = Client.objects.create(
            name=username[:30] if username else "Клиент",
            surname="Клиент",
            fathers_name=None,
            home_adress="—",
            mobile_number="—",
            email=email,
        )

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = Profile.Role.CLIENT
        profile.client = client
        profile.hotel = None
        profile.save(update_fields=["role", "client", "hotel"])

        return user
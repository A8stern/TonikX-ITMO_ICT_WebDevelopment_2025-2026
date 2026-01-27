from djoser.serializers import UserSerializer
from rest_framework import serializers
from .models import Profile
from .serializers import HotelSerializer, ClientSerializer  # из твоего serializers.py

class CurrentUserSerializer(UserSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    hotel = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = tuple(UserSerializer.Meta.fields) + ("role", "hotel", "client")

    def get_hotel(self, obj):
        prof = getattr(obj, "profile", None)
        if not prof or not prof.hotel_id:
            return None
        return HotelSerializer(prof.hotel).data

    def get_client(self, obj):
        prof = getattr(obj, "profile", None)
        if not prof or not prof.client_id:
            return None
        return ClientSerializer(prof.client).data
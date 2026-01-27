from rest_framework import serializers
from .models import (
    Hotel, RoomInHotel, TypeOfRoom, Convenience,
    Client, Staff, Booking, CheckIn, CleaningTime, Profile
)


class HotelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ["id_hotel", "city", "name", "num_of_rooms", "address", "image", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class RoomTypeInHotelSerializer(serializers.ModelSerializer):
    total_rooms = serializers.IntegerField()
    free_rooms = serializers.IntegerField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TypeOfRoom
        fields = ["id_type", "name", "num_of_places", "base_price", "total_rooms", "free_rooms", "image", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class TypeOfRoomSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TypeOfRoom
        fields = ["id_type", "name", "num_of_places", "base_price", "num_of_rooms", "num_of_free_rooms", "image", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url

class RoomTypeDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TypeOfRoom
        fields = ["id_type", "name", "num_of_places", "base_price", "image", "image_url"]

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class RoomShortSerializer(serializers.ModelSerializer):
    room_type = TypeOfRoomSerializer(read_only=True)

    class Meta:
        model = RoomInHotel
        fields = ["id_number", "room_number", "places_number", "status", "cleaned", "room_type"]


class RoomSerializer(serializers.ModelSerializer):
    hotel = HotelSerializer(read_only=True)
    room_type = TypeOfRoomSerializer(read_only=True)

    class Meta:
        model = RoomInHotel
        fields = ["id_number", "hotel", "room_type", "room_number", "places_number", "status", "cleaned"]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id_client", "name", "surname", "fathers_name", "home_adress", "mobile_number", "email"]


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ["id_staff", "contract", "full_name", "job_title"]


class BookingSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    staff = StaffSerializer(read_only=True)
    room_type = TypeOfRoomSerializer(read_only=True)
    hotel = HotelSerializer(read_only=True)   # <-- добавь

    class Meta:
        model = Booking
        fields = [
            "id_book", "book_status", "date_start", "date_end",
            "hotel",        # <-- добавь
            "client", "staff", "room_type",
            "price", "payed", "type_of_payment",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["book_status", "date_start", "date_end", "room_type", "price", "payed", "type_of_payment"]


class BookingPaySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=9, decimal_places=2)


class CheckInSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    room = RoomShortSerializer(read_only=True)
    staff = StaffSerializer(read_only=True)
    booking = BookingSerializer(read_only=True)

    class Meta:
        model = CheckIn
        fields = ["id_check_in", "date_check_in", "date_check_out", "client", "room", "staff", "booking"]


class CheckInCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckIn
        fields = ["date_check_in", "date_check_out", "client", "room", "booking"]


class CleaningSerializer(serializers.ModelSerializer):
    room = RoomShortSerializer(read_only=True)
    staff = StaffSerializer(read_only=True)

    class Meta:
        model = CleaningTime
        fields = ["id_cleaning", "room", "staff", "cleaning_time", "date", "cleaning_status"]


class CleaningCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CleaningTime
        fields = ["room", "cleaning_time", "date", "cleaning_status"]


class ProfileSerializer(serializers.ModelSerializer):
    hotel = HotelSerializer(read_only=True)
    client = ClientSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["role", "hotel", "client"]

class BookingAdminListSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    room_type = TypeOfRoomSerializer(read_only=True)
    hotel = HotelSerializer(read_only=True)

    room_number = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id_book",
            "book_status",
            "date_start",
            "date_end",
            "price",
            "payed",
            "type_of_payment",
            "hotel",
            "client",
            "room_type",
            "room_number",
        ]

    def get_room_number(self, obj):
        ch = obj.checkins.select_related("room").order_by("-id_check_in").first()
        return ch.room.room_number if ch else None


class BookingAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["date_start", "date_end", "book_status", "type_of_payment", "price", "payed"]

    def validate(self, attrs):
        ds = attrs.get("date_start", getattr(self.instance, "date_start", None))
        de = attrs.get("date_end", getattr(self.instance, "date_end", None))
        if ds and de and de < ds:
            raise serializers.ValidationError({"date_end": "date_end must be >= date_start"})
        return attrs


class BookingAdminCheckinSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()

class BookingAdminCheckoutSerializer(serializers.Serializer):
    date_check_out = serializers.DateField(required=False)

class BookingAdminChangeRoomSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()


class CleanerListSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    full_name = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    is_active = serializers.BooleanField()
    hotel_id = serializers.IntegerField()
    hotel_name = serializers.CharField()


class CleaningAdminSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(source="room.room_number", read_only=True)
    room_type_name = serializers.CharField(source="room.room_type.name", read_only=True)
    staff_name = serializers.CharField(source="staff.full_name", read_only=True)

    class Meta:
        model = CleaningTime
        fields = [
            "id_cleaning",
            "date",
            "cleaning_time",
            "cleaning_status",
            "room",          # id_number
            "room_number",
            "room_type_name",
            "staff",         # id_staff
            "staff_name",
        ]


class CleaningStatusUpdateSerializer(serializers.Serializer):
    cleaning_status = serializers.ChoiceField(choices=[("Убран", "Убран"), ("Не убран", "Не убран")])
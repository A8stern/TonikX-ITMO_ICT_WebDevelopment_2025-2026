from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Hotel, Amenity, RoomType, HotelRoomType, Reservation, Review


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "owner")


admin.site.register(Amenity)
admin.site.register(RoomType)


@admin.register(HotelRoomType)
class HotelRoomTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "hotel", "room_type", "total_units", "occupied_units", "capacity", "price_per_night")
    list_filter = ("hotel", "room_type")


@admin.action(description="Check-in selected reservations")
def check_in_reservations(modeladmin, request, queryset):
    for r in queryset.select_related("hotel_room_type"):
        try:
            r.mark_checked_in()
        except ValidationError as e:
            messages.error(request, f"Reservation #{r.pk}: {e}")


@admin.action(description="Check-out selected reservations")
def check_out_reservations(modeladmin, request, queryset):
    for r in queryset.select_related("hotel_room_type"):
        try:
            r.mark_checked_out()
        except ValidationError as e:
            messages.error(request, f"Reservation #{r.pk}: {e}")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "hotel_room_type", "check_in", "check_out", "status")
    list_filter = ("status", "hotel_room_type__hotel", "hotel_room_type__room_type")
    actions = [check_in_reservations, check_out_reservations]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "hotel_room_type", "rating", "created_at")
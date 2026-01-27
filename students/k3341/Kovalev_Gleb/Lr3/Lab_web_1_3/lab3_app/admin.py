from django.contrib import admin

from .models import (
    Hotel, TypeOfRoom,
    Staff, Client, RoomInHotel,
    Booking, BookingConvenience,
    CheckIn, CleaningTime, Profile
)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("id_hotel", "name", "city", "num_of_rooms", "address")
    search_fields = ("name", "city", "address")
    list_filter = ("city",)
    # если добавил ImageField image:
    # readonly_fields = ()
    # fields = (...)


@admin.register(TypeOfRoom)
class TypeOfRoomAdmin(admin.ModelAdmin):
    list_display = ("id_type", "name", "num_of_places", "base_price", "num_of_rooms", "num_of_free_rooms")
    search_fields = ("name",)
    list_filter = ("num_of_places",)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("id_staff", "full_name", "job_title", "contract")
    list_filter = ("job_title",)
    search_fields = ("full_name",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id_client", "surname", "name", "email", "mobile_number")
    search_fields = ("surname", "name", "email", "mobile_number")


@admin.register(RoomInHotel)
class RoomInHotelAdmin(admin.ModelAdmin):
    list_display = ("id_number", "hotel", "room_number", "places_number", "status", "cleaned", "room_type")
    list_filter = ("hotel", "status", "places_number", "room_type")
    search_fields = ("hotel__name", "room_number")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id_book", "book_status", "client", "room_type", "date_start", "date_end", "price", "payed", "type_of_payment")
    list_filter = ("book_status", "type_of_payment", "room_type")
    search_fields = ("client__surname", "client__name", "id_book")


@admin.register(BookingConvenience)
class BookingConvenienceAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "convenience")
    list_filter = ("convenience",)


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("id_check_in", "client", "room", "staff", "date_check_in", "date_check_out", "booking")
    list_filter = ("date_check_in", "date_check_out", "staff")
    search_fields = ("client__surname", "room__room_number")


@admin.register(CleaningTime)
class CleaningTimeAdmin(admin.ModelAdmin):
    list_display = ("id_cleaning", "room", "staff", "date", "cleaning_time", "cleaning_status")
    list_filter = ("date", "cleaning_status", "staff")
    search_fields = ("room__room_number", "staff__full_name")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "hotel", "client")
    list_filter = ("role", "hotel")
    search_fields = ("user__username",)
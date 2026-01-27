from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import HotelViewSet, RoomViewSet, ClientViewSet, AdminViewSet, CleanerViewSet, TypeOfRoomViewSet, AdminBookingsViewSet, AdminStaffViewSet

router = DefaultRouter()
router.register(r"hotels", HotelViewSet, basename="hotels")
router.register(r"room-types", TypeOfRoomViewSet, basename="room-types")
router.register(r"rooms", RoomViewSet, basename="rooms")

urlpatterns = [
    path("api/", include(router.urls)),

    # client
    path("api/client/me/", ClientViewSet.as_view({"get": "me"})),
    path("api/client/my-bookings/", ClientViewSet.as_view({"get": "my_bookings"})),
    path("api/client/book/", ClientViewSet.as_view({"post": "create_booking"})),
    path("api/client/bookings/<int:pk>/pay/", ClientViewSet.as_view({"post": "pay"})),
    path("api/client/bookings/<int:pk>/cancel/", ClientViewSet.as_view({"post": "cancel"})),

    # admin
    path("api/admin/hotel/", AdminViewSet.as_view({"get": "my_hotel"})),
    path("api/admin/rooms/", AdminViewSet.as_view({"get": "rooms"})),
    path("api/admin/residents/", AdminViewSet.as_view({"get": "residents"})),
    path("api/admin/checkin/", AdminViewSet.as_view({"post": "checkin"})),
    path("api/admin/checkins/<int:pk>/checkout/", AdminViewSet.as_view({"post": "checkout"})),
    path("api/admin/staff/", AdminViewSet.as_view({"post": "add_staff"})),
    path("api/admin/report/quarterly/", AdminViewSet.as_view({"get": "quarterly_report"})),

    path("api/admin/bookings/", AdminBookingsViewSet.as_view({"get": "list"})),
    path("api/admin/bookings/<int:pk>/", AdminBookingsViewSet.as_view({"patch": "partial_update"})),
    path("api/admin/bookings/<int:pk>/checkin/", AdminBookingsViewSet.as_view({"post": "checkin"})),
    path("api/admin/bookings/<int:pk>/checkout/", AdminBookingsViewSet.as_view({"post": "checkout"})),
    path("api/admin/bookings/<int:pk>/change-room/", AdminBookingsViewSet.as_view({"post": "change_room"})),

    path("api/admin/cleaners/", AdminStaffViewSet.as_view({"get": "list_cleaners"})),
    path("api/admin/cleaners/<int:staff_id>/stats/", AdminStaffViewSet.as_view({"get": "cleaner_stats"})),
    path("api/admin/cleaners/<int:staff_id>/fire/", AdminStaffViewSet.as_view({"post": "fire_cleaner"})),

    path("api/admin/cleanings/", AdminStaffViewSet.as_view({"get": "list_cleanings"})),
    path("api/admin/cleanings/<int:pk>/", AdminStaffViewSet.as_view({"patch": "update_cleaning"})),

    # cleaner
    path("api/cleaner/my-hotel/", CleanerViewSet.as_view({"get": "my_hotel"})),
    path("api/cleaner/rooms/", CleanerViewSet.as_view({"get": "rooms"})),
    path("api/cleaner/cleanings/", CleanerViewSet.as_view({"get": "cleanings", "post": "add_cleaning"})),
    path("api/cleaner/cleanings/<int:pk>/", CleanerViewSet.as_view({"delete": "delete_cleaning"})),
]
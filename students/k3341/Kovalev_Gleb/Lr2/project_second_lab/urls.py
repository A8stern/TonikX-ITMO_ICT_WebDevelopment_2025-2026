from django.urls import path
from . import views

urlpatterns = [
    path("", views.HotelListView.as_view(), name="home"),
    path("hotels/", views.HotelListView.as_view(), name="hotel_list"),

    path("hotels/<int:hotel_id>/", views.hotel_detail, name="hotel_detail"),
    path("hotels/<int:hotel_id>/guests-last-month/", views.hotel_guests_last_month, name="hotel_guests_last_month"),

    path("rooms/<int:room_id>/", views.room_detail, name="room_detail"),
    path("reservations/<int:reservation_id>/edit/", views.reservation_edit, name="reservation_edit"),

    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
]
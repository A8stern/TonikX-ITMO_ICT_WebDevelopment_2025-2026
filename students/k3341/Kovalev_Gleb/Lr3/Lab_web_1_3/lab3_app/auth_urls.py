from django.urls import path
from .auth_views import staff_register, client_register

urlpatterns = [
    path("staff/register/", staff_register),
    path("client/register/", client_register),
]
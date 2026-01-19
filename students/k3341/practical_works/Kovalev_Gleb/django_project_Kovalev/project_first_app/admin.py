from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Car, DriverLicense, Ownership

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Extra fields", {"fields": ("birth_date", "passport_number", "home_address", "nationality")}),
    )
    list_display = ("username", "last_name", "first_name", "passport_number", "nationality", "is_staff")


admin.site.register(Car)
admin.site.register(DriverLicense)
admin.site.register(Ownership)
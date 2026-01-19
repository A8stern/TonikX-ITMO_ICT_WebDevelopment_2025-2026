from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Car(models.Model):
    car_id = models.BigAutoField(primary_key=True)
    plate_number = models.CharField(max_length=15)
    brand = models.CharField(max_length=20)
    model = models.CharField(max_length=20)
    color = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = "car"

    def __str__(self):
        return f"{self.plate_number} ({self.brand} {self.model})"


class User(AbstractUser):
    passport_number = models.CharField(max_length=30, blank=True, null=True)
    home_address = models.CharField(max_length=255, blank=True, null=True)
    nationality = models.CharField(max_length=80, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    cars = models.ManyToManyField(
        Car,
        through="Ownership",
        related_name="owners",
        blank=True,
    )

    class Meta:
        db_table = "user"

    def __str__(self):
        full_name = f"{self.last_name} {self.first_name}".strip()
        return full_name if full_name else self.username


class DriverLicense(models.Model):
    license_id = models.BigAutoField(primary_key=True)

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_license",
    )

    license_number = models.CharField(max_length=10)
    license_type = models.CharField(max_length=10)
    issue_date = models.DateTimeField()

    class Meta:
        db_table = "driver_license"

    def __str__(self):
        return f"{self.license_number} ({self.license_type})"


class Ownership(models.Model):
    ownership_id = models.BigAutoField(primary_key=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ownerships",
    )
    car = models.ForeignKey(
        Car,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ownerships",
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ownership"

    def __str__(self):
        return f"{self.owner} -> {self.car} ({self.start_date}..{self.end_date})"
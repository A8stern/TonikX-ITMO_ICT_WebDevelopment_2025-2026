from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError


class Hotel(models.Model):
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_hotels",
    )
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "hotel"

    def __str__(self) -> str:
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "amenity"

    def __str__(self) -> str:
        return self.name


class RoomType(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    amenities = models.ManyToManyField(Amenity, blank=True, related_name="room_types")

    class Meta:
        db_table = "room_type"
        unique_together = ("title",)

    def __str__(self) -> str:
        return self.title


class HotelRoomType(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="hotel_room_types")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="hotel_variants")

    capacity = models.PositiveSmallIntegerField()

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    total_units = models.PositiveIntegerField(default=0)

    occupied_units = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "hotel_room_type"
        unique_together = ("hotel", "room_type")

    def __str__(self) -> str:
        return f"{self.hotel.name} — {self.room_type.title}"

    @property
    def available_units(self) -> int:
        return max(self.total_units - self.occupied_units, 0)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.occupied_units > self.total_units:
            raise ValidationError("occupied_units cannot be greater than total_units")


class Reservation(models.Model):
    class Status(models.TextChoices):
        BOOKED = "BOOKED", "Booked"
        CHECKED_IN = "CHECKED_IN", "Checked in"
        CHECKED_OUT = "CHECKED_OUT", "Checked out"
        CANCELED = "CANCELED", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    hotel_room_type = models.ForeignKey(
        HotelRoomType,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    check_in = models.DateField()
    check_out = models.DateField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    actual_check_in = models.DateTimeField(null=True, blank=True)
    actual_check_out = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reservation"
        indexes = [
            models.Index(fields=["hotel_room_type", "check_in", "check_out"]),
            models.Index(fields=["status", "check_in"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.hotel_room_type} ({self.check_in}..{self.check_out})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValidationError("check_out must be after check_in")

    @property
    def hotel(self) -> Hotel:
        return self.hotel_room_type.hotel

    def mark_checked_in(self):
        if self.status != self.Status.BOOKED:
            return

        with transaction.atomic():
            hrt = type(self).objects.select_related("hotel_room_type").select_for_update().get(
                pk=self.pk).hotel_room_type
            hrt = hrt.__class__.objects.select_for_update().get(pk=hrt.pk)

            if hrt.occupied_units >= hrt.total_units:
                raise ValidationError("No free units to check-in right now.")

            hrt.occupied_units += 1
            hrt.save(update_fields=["occupied_units"])

            self.status = self.Status.CHECKED_IN
            self.actual_check_in = timezone.now()
            self.save(update_fields=["status", "actual_check_in", "updated_at"])

    def mark_checked_out(self):
        if self.status != self.Status.CHECKED_IN:
            return

        with transaction.atomic():
            hrt = type(self).objects.select_related("hotel_room_type").select_for_update().get(
                pk=self.pk).hotel_room_type
            hrt = hrt.__class__.objects.select_for_update().get(pk=hrt.pk)

            if hrt.occupied_units > 0:
                hrt.occupied_units -= 1
                hrt.save(update_fields=["occupied_units"])

            self.status = self.Status.CHECKED_OUT
            self.actual_check_out = timezone.now()
            self.save(update_fields=["status", "actual_check_out", "updated_at"])


class Review(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    hotel_room_type = models.ForeignKey(
        HotelRoomType,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    stay_from = models.DateField()
    stay_to = models.DateField()

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review"
        indexes = [
            models.Index(fields=["hotel_room_type", "created_at"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self) -> str:
        return f"Review {self.rating}/10 by {self.author}"
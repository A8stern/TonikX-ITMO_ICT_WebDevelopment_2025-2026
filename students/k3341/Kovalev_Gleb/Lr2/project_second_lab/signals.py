from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Reservation, HotelRoomType


@receiver(pre_save, sender=Reservation)
def reservation_status_change(sender, instance: Reservation, **kwargs):
    if not instance.pk:
        return  # новая бронь — occupied_units не трогаем

    prev = Reservation.objects.select_related("hotel_room_type").get(pk=instance.pk)
    if prev.status == instance.status:
        return

    # BOOKED -> CHECKED_IN : +1
    if prev.status == Reservation.Status.BOOKED and instance.status == Reservation.Status.CHECKED_IN:
        with transaction.atomic():
            hrt = HotelRoomType.objects.select_for_update().get(pk=instance.hotel_room_type_id)
            if hrt.occupied_units >= hrt.total_units:
                raise ValidationError("No free units to check-in right now.")
            hrt.occupied_units += 1
            hrt.save(update_fields=["occupied_units"])

    # CHECKED_IN -> CHECKED_OUT : -1
    if prev.status == Reservation.Status.CHECKED_IN and instance.status == Reservation.Status.CHECKED_OUT:
        with transaction.atomic():
            hrt = HotelRoomType.objects.select_for_update().get(pk=instance.hotel_room_type_id)
            if hrt.occupied_units > 0:
                hrt.occupied_units -= 1
                hrt.save(update_fields=["occupied_units"])

    # CHECKED_IN -> CANCELED (если такое разрешишь): -1
    if prev.status == Reservation.Status.CHECKED_IN and instance.status == Reservation.Status.CANCELED:
        with transaction.atomic():
            hrt = HotelRoomType.objects.select_for_update().get(pk=instance.hotel_room_type_id)
            if hrt.occupied_units > 0:
                hrt.occupied_units -= 1
                hrt.save(update_fields=["occupied_units"])
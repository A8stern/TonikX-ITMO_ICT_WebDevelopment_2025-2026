from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from lab3_app.models import Hotel, TypeOfRoom, RoomInHotel


class Command(BaseCommand):
    help = "Create RoomInHotel for each Hotel based on TypeOfRoom.num_of_rooms (global types)."

    def add_arguments(self, parser):
        parser.add_argument("--hotel", type=int, default=None, help="id_hotel, if not set -> all hotels")
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="If set, create only missing rooms up to TypeOfRoom.num_of_rooms per type per hotel",
        )
        parser.add_argument(
            "--start-number",
            type=int,
            default=None,
            help="Starting room_number if hotel has no rooms. If not set -> starts from 1",
        )
        parser.add_argument(
            "--status",
            type=str,
            default="Свободен",
            help="Default status for created rooms",
        )
        parser.add_argument("--cleaned", action="store_true", help="Set cleaned=True for created rooms")

    @transaction.atomic
    def handle(self, *args, **opts):
        hotels = Hotel.objects.all()
        if opts["hotel"]:
            hotels = hotels.filter(id_hotel=opts["hotel"])

        if not hotels.exists():
            self.stderr.write(self.style.ERROR("Отели не найдены."))
            return

        types = list(TypeOfRoom.objects.all().order_by("id_type"))
        if not types:
            self.stderr.write(self.style.ERROR("В базе нет TypeOfRoom. Сначала создай типы номеров."))
            return

        status = opts["status"]
        cleaned = bool(opts["cleaned"])
        only_missing = bool(opts["only_missing"])

        total_created = 0

        for hotel in hotels:
            # старт номера: max(room_number)+1 или start-number/1
            mx = RoomInHotel.objects.filter(hotel=hotel).aggregate(m=Max("room_number"))["m"]
            if mx is not None:
                next_number = mx + 1
            else:
                next_number = int(opts["start_number"] or 1)

            created_for_hotel = 0

            for t in types:
                target = int(t.num_of_rooms)

                if only_missing:
                    already = RoomInHotel.objects.filter(hotel=hotel, room_type=t).count()
                    need = max(target - already, 0)
                else:
                    # создаём ровно target, даже если уже есть (может привести к дубликатам по типу)
                    # поэтому лучше использовать only_missing
                    need = target

                for _ in range(need):
                    # гарантируем уникальность room_number в отеле
                    while RoomInHotel.objects.filter(hotel=hotel, room_number=next_number).exists():
                        next_number += 1

                    RoomInHotel.objects.create(
                        hotel=hotel,
                        room_type=t,
                        room_number=next_number,
                        places_number=t.num_of_places,
                        status=status,
                        cleaned=cleaned,
                    )
                    next_number += 1
                    created_for_hotel += 1

            self.stdout.write(self.style.SUCCESS(
                f"Hotel {hotel.id_hotel} ({hotel.name}): created {created_for_hotel} rooms"
            ))
            total_created += created_for_hotel

        self.stdout.write(self.style.SUCCESS(f"Done. Total created={total_created}"))
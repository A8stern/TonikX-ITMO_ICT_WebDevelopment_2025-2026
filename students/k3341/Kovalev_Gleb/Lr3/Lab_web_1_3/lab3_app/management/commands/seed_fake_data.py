import random
from datetime import date, timedelta, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import now

from lab3_app.models import (
    Hotel, TypeOfRoom, Convenience, ConvenienceType,
    ContractNumber, Staff, Client, RoomInHotel,
    Booking, BookingConvenience, CheckIn, CleaningTime, Profile
)

User = get_user_model()


FIRST_NAMES = ["Иван", "Пётр", "Алина", "Мария", "София", "Даниил", "Егор", "Кирилл", "Ольга", "Анна"]
LAST_NAMES = ["Иванов", "Петров", "Смирнов", "Кузнецов", "Попов", "Соколов", "Лебедев", "Козлов", "Новиков", "Морозов"]
PATRONYMICS = ["Иванович", "Петрович", "Алексеевич", "Сергеевич", "Андреевич", "Дмитриевич", "Олегович", None]
CITIES = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Самара"]


def rand_full_name():
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    pt = random.choice(PATRONYMICS)
    return f"{ln} {fn}" + (f" {pt}" if pt else "")


def rand_phone():
    return f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"


class Command(BaseCommand):
    help = "Seed fake data for hotel system"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")
        parser.add_argument("--hotels", type=int, default=3)
        parser.add_argument("--rooms-per-hotel", type=int, default=18)
        parser.add_argument("--clients", type=int, default=25)
        parser.add_argument("--bookings", type=int, default=30)

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["clear"]:
            self._clear()

        hotels = self._seed_hotels(opts["hotels"])
        room_types = self._seed_room_types()
        conveniences = self._seed_conveniences()
        self._seed_convenience_type(room_types, conveniences)

        rooms = self._seed_rooms(hotels, room_types, opts["rooms_per_hotel"])
        contracts = self._seed_contracts()

        staff = self._seed_staff(contracts, count_admin=opts["hotels"], count_cleaners=opts["hotels"] * 2)
        clients = self._seed_clients(opts["clients"])

        bookings = self._seed_bookings(clients, staff, room_types, opts["bookings"])
        self._seed_checkins(bookings, rooms)
        self._seed_cleanings(rooms, staff)

        self._seed_users_and_profiles(hotels, staff, clients)

        self.stdout.write(self.style.SUCCESS("✅ Fake data seeded successfully."))

    def _clear(self):
        # Важно: порядок из-за FK/PROTECT
        CleaningTime.objects.all().delete()
        CheckIn.objects.all().delete()
        BookingConvenience.objects.all().delete()
        Booking.objects.all().delete()
        RoomInHotel.objects.all().delete()
        Staff.objects.all().delete()
        ContractNumber.objects.all().delete()
        ConvenienceType.objects.all().delete()
        Convenience.objects.all().delete()
        TypeOfRoom.objects.all().delete()
        Profile.objects.all().delete()
        Client.objects.all().delete()
        Hotel.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        self.stdout.write(self.style.WARNING("🧹 Cleared existing data (except superuser)."))

    def _seed_hotels(self, n: int):
        hotels = []
        for i in range(n):
            h, _ = Hotel.objects.get_or_create(
                name=f"Hotel_{i+1}",
                city=random.choice(CITIES),
                defaults={
                    "num_of_rooms": 1,
                    "address": f"Street {i+1}, {random.randint(1, 99)}",
                }
            )
            # num_of_rooms уточним после генерации номеров
            hotels.append(h)
        return hotels

    def _seed_room_types(self):
        # 3 типа из задания: 1/2/3 местные
        types = [
            ("Одноместный", 1, 3500),
            ("Двухместный", 2, 5200),
            ("Трехместный", 3, 6900),
        ]
        res = []
        for name, places, price in types:
            obj, _ = TypeOfRoom.objects.get_or_create(
                name=name,
                defaults={
                    "num_of_rooms": 1,
                    "num_of_places": places,
                    "base_price": price,
                    "num_of_free_rooms": 0,
                }
            )
            res.append(obj)
        return res

    def _seed_conveniences(self):
        data = [
            ("Wi-Fi", "Бесплатный интернет"),
            ("TV", "Телевизор в номере"),
            ("Кондиционер", "Кондиционер"),
            ("Завтрак", "Завтрак включен"),
            ("Сейф", "Сейф в номере"),
        ]
        res = []
        for name, desc in data:
            c, _ = Convenience.objects.get_or_create(name=name, defaults={"description": desc})
            res.append(c)
        return res

    def _seed_convenience_type(self, room_types, conveniences):
        # Привяжем 2-4 удобства к каждому типу
        for rt in room_types:
            chosen = random.sample(conveniences, k=random.randint(2, min(4, len(conveniences))))
            for idx, conv in enumerate(chosen, start=1):
                ConvenienceType.objects.get_or_create(
                    room_type=rt,
                    convenience=conv,
                    defaults={"num": idx},
                )

    def _seed_rooms(self, hotels, room_types, rooms_per_hotel: int):
        rooms = []
        for h in hotels:
            # распределим типы случайно
            for i in range(rooms_per_hotel):
                rt = random.choice(room_types)
                room_number = 100 + i + 1  # 101, 102...
                room = RoomInHotel.objects.create(
                    hotel=h,
                    room_type=rt,
                    room_number=room_number,
                    places_number=rt.num_of_places,
                    status="Свободен",
                    cleaned=bool(random.getrandbits(1)),
                )
                rooms.append(room)

            h.num_of_rooms = rooms_per_hotel
            h.save(update_fields=["num_of_rooms"])

        # обновим агрегаты в типах (сколько номеров каждого типа)
        for rt in room_types:
            total = RoomInHotel.objects.filter(room_type=rt).count()
            rt.num_of_rooms = max(1, total)
            rt.num_of_free_rooms = total  # пока всё свободно
            rt.save(update_fields=["num_of_rooms", "num_of_free_rooms"])

        return rooms

    def _seed_contracts(self):
        contracts = []
        today = date.today()
        for i in range(1, 21):
            start = today - timedelta(days=random.randint(0, 60))
            end = start + timedelta(days=random.randint(90, 365))
            c, _ = ContractNumber.objects.get_or_create(
                contract_number=1000 + i,
                defaults={
                    "beginning_of_contract": start,
                    "end_of_contract": end,
                    "number_of_job_days": random.randint(18, 26),
                    "type_of_contract": random.choice(["Постоянный", "Сезонный"]),
                    "conditions": "Стандартные условия",
                }
            )
            contracts.append(c)
        return contracts

    def _seed_staff(self, contracts, count_admin: int, count_cleaners: int):
        staff = []

        # Администраторы
        for i in range(count_admin):
            s = Staff.objects.create(
                contract=random.choice(contracts),
                full_name=rand_full_name(),
                job_title="Администратор",
            )
            staff.append(s)

        # Уборщики
        for i in range(count_cleaners):
            s = Staff.objects.create(
                contract=random.choice(contracts),
                full_name=rand_full_name(),
                job_title="Уборщик",
            )
            staff.append(s)

        # Техник + охранник
        for title in ["Техник", "Охранник"]:
            for _ in range(2):
                s = Staff.objects.create(
                    contract=random.choice(contracts),
                    full_name=rand_full_name(),
                    job_title=title,
                )
                staff.append(s)

        return staff

    def _seed_clients(self, n: int):
        clients = []
        for i in range(n):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            pt = random.choice(PATRONYMICS)

            c = Client.objects.create(
                name=fn,
                surname=ln,
                fathers_name=pt,
                home_adress=f"{random.choice(CITIES)}, ул. {random.randint(1, 50)}, д.{random.randint(1, 120)}",
                mobile_number=rand_phone(),
                email=f"user{i+1}@mail.com",
            )
            clients.append(c)
        return clients

    def _seed_bookings(self, clients, staff, room_types, n: int):
        bookings = []
        today = date.today()

        admins = [s for s in staff if s.job_title == "Администратор"]
        if not admins:
            admins = staff[:1]

        for _ in range(n):
            start = today + timedelta(days=random.randint(-15, 20))
            end = start + timedelta(days=random.randint(1, 7))
            rt = random.choice(room_types)

            days = (end - start).days + 1
            price = Decimal(days * rt.base_price)

            status = random.choice(["Ожидает оплату", "Забронирован"])
            payed = Decimal("0.00")
            if status == "Забронирован":
                # часть оплачена полностью
                payed = price if random.random() < 0.6 else price * Decimal("0.5")

            b = Booking.objects.create(
                book_status=status,
                date_start=start,
                date_end=end,
                client=random.choice(clients),
                staff=random.choice(admins),
                room_type=rt,
                price=price,
                payed=payed,
                type_of_payment=random.choice(["Карта", "СБП", "Наличные"]),
            )

            # добавим 0-2 доп. удобства
            convs = list(Convenience.objects.all())
            if convs and random.random() < 0.5:
                for conv in random.sample(convs, k=random.randint(0, min(2, len(convs)))):
                    BookingConvenience.objects.get_or_create(booking=b, convenience=conv)

            bookings.append(b)

        return bookings

    def _seed_checkins(self, bookings, rooms):
        # заселим часть броней, подбирая свободный номер нужного типа
        today = date.today()

        for b in bookings:
            if random.random() > 0.45:
                continue

            # выберем свободную комнату соответствующего типа
            candidates = [r for r in rooms if r.room_type_id == b.room_type_id and r.status == "Свободен"]
            if not candidates:
                continue

            room = random.choice(candidates)

            # создаём checkin на интервал брони
            CheckIn.objects.create(
                date_check_in=b.date_start,
                date_check_out=b.date_end,
                client=b.client,
                room=room,
                staff=b.staff,
                booking=b,
            )

            # обновим комнату + free_rooms счетчики
            room.status = "Занят"
            room.cleaned = False
            room.save(update_fields=["status", "cleaned"])

            b.book_status = "Заселен"
            b.save(update_fields=["book_status"])

            rt = b.room_type
            rt.num_of_free_rooms = max(0, rt.num_of_free_rooms - 1)
            rt.save(update_fields=["num_of_free_rooms"])

    def _seed_cleanings(self, rooms, staff):
        cleaners = [s for s in staff if s.job_title == "Уборщик"]
        if not cleaners:
            return

        today = date.today()
        # сделаем уборки за последние 5 дней
        for _ in range(40):
            room = random.choice(rooms)
            d = today - timedelta(days=random.randint(0, 5))
            t = time(hour=random.randint(9, 18), minute=random.choice([0, 15, 30, 45]))

            CleaningTime.objects.update_or_create(
                room=room,
                date=d,
                defaults={
                    "staff": random.choice(cleaners),
                    "cleaning_time": t,
                    "cleaning_status": random.choice(["Убран", "Не убран"]),
                }
            )

    def _seed_users_and_profiles(self, hotels, staff, clients):
        # admin user per hotel
        for idx, h in enumerate(hotels, start=1):
            username = f"admin{idx}"
            u = User.objects.filter(username=username).first()
            if not u:
                u = User.objects.create_user(username=username, password="admin12345")
            prof, _ = Profile.objects.get_or_create(user=u)
            prof.role = Profile.Role.ADMIN
            prof.hotel = h
            prof.client = None
            prof.save()

        # cleaner users (2)
        for idx in range(1, 3):
            username = f"cleaner{idx}"
            u = User.objects.filter(username=username).first()
            if not u:
                u = User.objects.create_user(username=username, password="cleaner12345")
            prof, _ = Profile.objects.get_or_create(user=u)
            prof.role = Profile.Role.CLEANER
            prof.hotel = random.choice(hotels)
            prof.client = None
            prof.save()

        # one client user linked to Client
        username = "client1"
        u = User.objects.filter(username=username).first()
        if not u:
            u = User.objects.create_user(username=username, password="client12345")
        prof, _ = Profile.objects.get_or_create(user=u)
        prof.role = Profile.Role.CLIENT
        prof.hotel = None
        prof.client = random.choice(clients)
        prof.save()

        self.stdout.write(self.style.SUCCESS(
            "Created users: admin1..adminN (admin12345), cleaner1..2 (cleaner12345), client1 (client12345)"
        ))
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum, Min
from django.utils.dateparse import parse_date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import (
    Profile, Hotel, RoomInHotel, Client, Staff, Booking, CheckIn, CleaningTime, TypeOfRoom,
    RoomTypeAvailability,
)
from .serializers import (
    HotelSerializer, RoomSerializer, RoomShortSerializer,
    ClientSerializer, StaffSerializer, RoomTypeInHotelSerializer,
    BookingSerializer, BookingCreateSerializer, BookingPaySerializer,
    CheckInSerializer, CheckInCreateSerializer,
    CleaningSerializer, CleaningCreateSerializer,
    ProfileSerializer, TypeOfRoomSerializer, RoomTypeDetailSerializer,
    BookingAdminListSerializer, BookingAdminUpdateSerializer,
    BookingAdminCheckinSerializer, BookingAdminCheckoutSerializer,
    BookingAdminChangeRoomSerializer,
    CleanerListSerializer, CleaningAdminSerializer, CleaningStatusUpdateSerializer
)
from .permissions import IsAdmin, IsCleaner, IsClient

from django.db.models import Min

from rest_framework.pagination import PageNumberPagination

from rest_framework.authtoken.models import Token

# --------------------
# helpers
# --------------------

def _parse_required(request, name: str) -> date:
    s = request.query_params.get(name) or request.data.get(name)
    d = parse_date(s) if s else None
    if not d:
        raise ValueError(f"Missing/invalid date param: {name}")
    return d


def _quarter_range(year: int, quarter: int):
    if quarter not in (1, 2, 3, 4):
        raise ValueError("quarter must be 1..4")
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2
    start = date(year, start_month, 1)
    last = monthrange(year, end_month)[1]
    end = date(year, end_month, last)
    return start, end


def overlaps_checkin(qs, start, end):
    return qs.filter(date_check_in__lte=end, date_check_out__gte=start)


def admin_hotel(request):
    return getattr(request.user.profile, "hotel", None)


def client_obj(request):
    return getattr(request.user.profile, "client", None)


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def ensure_availability(hotel: Hotel, room_type: TypeOfRoom, start: date, end: date):
    """
    Создаёт/инициализирует строки доступности по дням.
    free_rooms = total_rooms_in_hotel_for_type - bookings_overlapping_that_day (кроме отменённых).
    """
    total = RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).count()

    for d in daterange(start, end):
        obj, created = RoomTypeAvailability.objects.get_or_create(
            hotel=hotel,
            room_type=room_type,
            day=d,
            defaults={"free_rooms": total},
        )
        if created:
            occupied = Booking.objects.filter(
                hotel=hotel,
                room_type=room_type,
                date_start__lte=d,
                date_end__gte=d,
            ).exclude(book_status="Отменен").count()
            obj.free_rooms = max(total - occupied, 0)
            obj.save(update_fields=["free_rooms"])


class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


CANCELLED = "Отменен"
CHECKED_OUT = "Выселен"
CHECKED_IN = "Заселен"


def _daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _recompute_availability(hotel, room_type, start, end):
    """
    Надёжный пересчёт free_rooms по дням на отрезке [start..end].
    free_rooms = total_rooms - active_bookings_count(day)
    """
    total = RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).count()

    for d in _daterange(start, end):
        occupied = (
            Booking.objects.filter(
                hotel=hotel,
                room_type=room_type,
                date_start__lte=d,
                date_end__gte=d,
            )
            .exclude(book_status__in=[CANCELLED, CHECKED_OUT])
            .count()
        )

        obj, _ = RoomTypeAvailability.objects.get_or_create(
            hotel=hotel,
            room_type=room_type,
            day=d,
            defaults={"free_rooms": max(total - occupied, 0)},
        )
        new_free = max(total - occupied, 0)
        if obj.free_rooms != new_free:
            obj.free_rooms = new_free
            obj.save(update_fields=["free_rooms"])


def _admin_hotel(request):
    return getattr(request.user.profile, "hotel", None)


def _admin_staff(request):
    return getattr(request.user.profile, "staff", None)


def _room_is_free_for_period(room, start, end):
    # комната свободна, если нет пересекающегося checkin
    return not CheckIn.objects.filter(
        room=room,
        date_check_in__lte=end,
        date_check_out__gte=start,
    ).exists()

# --------------------
# HOTEL endpoints (public read + admin update for images)
# --------------------

class HotelViewSet(viewsets.ModelViewSet):
    """
    Public:
      GET /api/hotels/
      GET /api/hotels/{id}/
      GET /api/hotels/{id}/room-types/
      GET /api/hotels/{id}/room-types/{type_id}/
      GET /api/hotels/{id}/room-types/{type_id}/availability?start=...&end=...
    Client (auth client):
      POST /api/hotels/{id}/room-types/{type_id}/book  {date_start, date_end, type_of_payment?}
    Admin:
      PATCH/PUT /api/hotels/{id}/  (multipart with image)
    """
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        # public read endpoints
        if self.action in (
            "list", "retrieve", "room_types", "rooms",
            "room_type_detail", "room_type_availability",
        ):
            return [AllowAny()]

        # booking must be client
        if self.action in ("book_room_type",):
            return [IsAuthenticated(), IsClient()]

        # write/update hotel (images) only admin
        return [IsAuthenticated(), IsAdmin()]

    # ---------- existing actions ----------

    @action(detail=True, methods=["get"], url_path="room-types")
    def room_types(self, request, pk=None):
        hotel = self.get_object()

        qs = (
            TypeOfRoom.objects
            .filter(rooms__hotel=hotel)
            .annotate(
                total_rooms=Count("rooms", distinct=True),
                free_rooms=Count("rooms", filter=Q(rooms__hotel=hotel, rooms__status="Свободен"), distinct=True),
            )
            .distinct()
            .order_by("num_of_places", "base_price")
        )

        return Response({
            "hotel": HotelSerializer(hotel, context={"request": request}).data,
            "room_types": RoomTypeInHotelSerializer(qs, many=True, context={"request": request}).data,
        })

    @action(detail=True, methods=["get"], url_path="rooms")
    def rooms(self, request, pk=None):
        hotel = self.get_object()
        qs = RoomInHotel.objects.filter(hotel=hotel).select_related("room_type").order_by("room_number")
        return Response(RoomShortSerializer(qs, many=True).data)

    # ---------- NEW: type detail in hotel ----------

    @action(detail=True, methods=["get"], url_path=r"room-types/(?P<type_id>\d+)")
    def room_type_detail(self, request, pk=None, type_id=None):
        hotel = self.get_object()
        room_type = TypeOfRoom.objects.filter(id_type=type_id).first()
        if not room_type:
            return Response({"detail": "room type not found"}, status=404)

        if not RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).exists():
            return Response({"detail": "this room type is not available in this hotel"}, status=400)

        return Response({
            "hotel": HotelSerializer(hotel, context={"request": request}).data,
            "room_type": RoomTypeDetailSerializer(room_type, context={"request": request}).data,
        })

    # ---------- NEW: availability by period ----------

    @action(detail=True, methods=["get"], url_path=r"room-types/(?P<type_id>\d+)/availability")
    def room_type_availability(self, request, pk=None, type_id=None):
        hotel = self.get_object()
        room_type = TypeOfRoom.objects.filter(id_type=type_id).first()
        if not room_type:
            return Response({"detail": "room type not found"}, status=404)

        try:
            start = _parse_required(request, "start")
            end = _parse_required(request, "end")
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        if end < start:
            return Response({"detail": "end must be >= start"}, status=400)

        if not RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).exists():
            return Response({"detail": "this room type is not available in this hotel"}, status=400)

        ensure_availability(hotel, room_type, start, end)

        days_qs = RoomTypeAvailability.objects.filter(
            hotel=hotel, room_type=room_type, day__range=(start, end)
        )
        min_free = days_qs.aggregate(m=Min("free_rooms"))["m"]

        return Response({
            "hotel_id": hotel.id_hotel,
            "room_type_id": room_type.id_type,
            "period": {"start": str(start), "end": str(end)},
            "min_free_rooms": min_free,
            "can_book": bool(min_free and min_free > 0),
        })

    # ---------- NEW: create booking (decrease availability per day) ----------

    @action(detail=True, methods=["post"], url_path=r"room-types/(?P<type_id>\d+)/book")
    @transaction.atomic
    def book_room_type(self, request, pk=None, type_id=None):
        hotel = self.get_object()
        room_type = TypeOfRoom.objects.filter(id_type=type_id).first()
        if not room_type:
            return Response({"detail": "room type not found"}, status=404)

        if not RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).exists():
            return Response({"detail": "this room type is not available in this hotel"}, status=400)

        cl = client_obj(request)
        if not cl:
            return Response({"detail": "profile.client is not set"}, status=400)

        try:
            start = _parse_required(request, "date_start")
            end = _parse_required(request, "date_end")
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        if end < start:
            return Response({"detail": "date_end must be >= date_start"}, status=400)

        if (end - start).days > 60:
            return Response({"detail": "max booking period is 60 days"}, status=400)

        pay_type = request.data.get("type_of_payment", "Карта")

        ensure_availability(hotel, room_type, start, end)

        # lock days
        days_qs = RoomTypeAvailability.objects.select_for_update().filter(
            hotel=hotel, room_type=room_type, day__range=(start, end)
        )
        expected = (end - start).days + 1
        if days_qs.count() != expected:
            return Response({"detail": "availability rows mismatch"}, status=400)

        min_free = days_qs.aggregate(m=Min("free_rooms"))["m"]
        if not min_free or min_free <= 0:
            return Response({"detail": "No free rooms for this period"}, status=400)

        for row in days_qs:
            row.free_rooms -= 1
            row.save(update_fields=["free_rooms"])

        staff = Staff.objects.filter(job_title="Администратор").first()
        if not staff:
            return Response({"detail": "No staff with job_title='Администратор' exists"}, status=400)

        nights = (end - start).days + 1
        price = Decimal(nights * room_type.base_price)

        booking = Booking.objects.create(
            book_status="Ожидает оплату",
            date_start=start,
            date_end=end,
            client=cl,
            staff=staff,
            room_type=room_type,
            hotel=hotel,  # IMPORTANT
            price=price,
            payed=Decimal("0.00"),
            type_of_payment=pay_type,
        )

        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )


# --------------------
# TypeOfRoom endpoints (admin edit images)
# --------------------

class TypeOfRoomViewSet(viewsets.ModelViewSet):
    queryset = TypeOfRoom.objects.all()
    serializer_class = TypeOfRoomSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdmin()]


# --------------------
# Rooms (read)
# --------------------

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RoomInHotel.objects.select_related("hotel", "room_type").all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]


# --------------------
# Client endpoints
# --------------------

class ClientViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsClient]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(ProfileSerializer(request.user.profile).data)

    @action(detail=False, methods=["get"], url_path="my-bookings")
    def my_bookings(self, request):
        cl = client_obj(request)
        if not cl:
            return Response({"detail": "profile.client is not set"}, status=400)
        qs = Booking.objects.select_related("room_type", "staff").filter(client=cl).order_by("-date_start")
        return Response(BookingSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=False, methods=["post"], url_path="book")
    def create_booking(self, request):
        """
        Старый эндпоинт бронирования — оставлен как есть (но лучше использовать /api/hotels/{id}/room-types/{type_id}/book)
        """
        cl = client_obj(request)
        if not cl:
            return Response({"detail": "profile.client is not set"}, status=400)

        ser = BookingCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        room_type = ser.validated_data["room_type"]
        start = ser.validated_data["date_start"]
        end = ser.validated_data["date_end"]
        if end < start:
            return Response({"detail": "date_end must be >= date_start"}, status=400)

        room_exists = RoomInHotel.objects.filter(room_type=room_type).select_related("hotel").first()
        if not room_exists:
            return Response({"detail": "No rooms with this type exist in any hotel"}, status=400)

        hotel = room_exists.hotel
        staff = Staff.objects.filter(job_title="Администратор").first()
        if not staff:
            return Response({"detail": "No staff with job_title='Администратор' exists. Create staff first."}, status=400)

        booking = ser.save(client=cl, staff=staff, hotel=hotel)
        # если у тебя уже добавлено поле booking.hotel — проставим:
        if hasattr(booking, "hotel_id"):
            booking.hotel = hotel
            booking.save(update_fields=["hotel"])

        return Response(BookingSerializer(booking, context={"request": request}).data, status=201)

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        cl = client_obj(request)
        if not cl:
            return Response({"detail": "profile.client is not set"}, status=400)

        booking = Booking.objects.filter(pk=pk, client=cl).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        ser = BookingPaySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        amount = ser.validated_data["amount"]

        new_payed = booking.payed + amount
        if new_payed > booking.price:
            return Response({"detail": "amount exceeds remaining price"}, status=400)

        booking.payed = new_payed
        if booking.payed == booking.price and booking.book_status == "Ожидает оплату":
            booking.book_status = "Забронирован"
        booking.save(update_fields=["payed", "book_status"])

        return Response(BookingSerializer(booking, context={"request": request}).data)

    def _daterange(start: date, end: date):
        cur = start
        while cur <= end:
            yield cur
            cur += timedelta(days=1)

    @action(detail=True, methods=["post"], url_path="cancel")
    @transaction.atomic
    def cancel(self, request, pk=None):
        """
        Отмена брони клиентом. Разрешаем только если статус = "Забронирован"
        POST /api/client/bookings/<id>/cancel/
        """
        cl = client_obj(request)
        if not cl:
            return Response({"detail": "profile.client is not set"}, status=400)

        booking = Booking.objects.select_for_update().filter(pk=pk, client=cl).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        if booking.book_status not in ("Забронирован", "Ожидает оплату"):
            return Response(
                {"detail": "Можно отменить только бронирование со статусом 'Забронирован' или 'Ожидает оплату'."},
                status=400)

        if not getattr(booking, "hotel_id", None):
            return Response({"detail": "booking.hotel is not set (add hotel field and fill it)."}, status=400)

        hotel = booking.hotel
        room_type = booking.room_type

        # вернём доступность на каждый день (если строки есть)
        days = list(daterange(booking.date_start, booking.date_end))
        qs = RoomTypeAvailability.objects.select_for_update().filter(
            hotel=hotel,
            room_type=room_type,
            day__in=days
        )

        total = RoomInHotel.objects.filter(hotel=hotel, room_type=room_type).count()

        for row in qs:
            row.free_rooms = min(row.free_rooms + 1, total)
            row.save(update_fields=["free_rooms"])

        booking.book_status = "Отменен"
        booking.save(update_fields=["book_status"])

        return Response(BookingSerializer(booking, context={"request": request}).data)


# --------------------
# Admin endpoints
# --------------------

class AdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=False, methods=["get"], url_path="hotel")
    def my_hotel(self, request):
        hotel = admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)
        return Response(HotelSerializer(hotel, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="rooms")
    def rooms(self, request):
        hotel = admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        qs = RoomInHotel.objects.filter(hotel=hotel).select_related("room_type").order_by("room_number")

        # ---- filters ----
        type_id = request.query_params.get("type_id")
        if type_id:
            qs = qs.filter(room_type_id=type_id)

        cleaned = request.query_params.get("cleaned")
        if cleaned is not None and cleaned != "":
            val = cleaned.lower()
            if val in ("true", "1", "yes"):
                qs = qs.filter(cleaned=True)
            elif val in ("false", "0", "no"):
                qs = qs.filter(Q(cleaned=False) | Q(cleaned__isnull=True))

        status = request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        search = request.query_params.get("search")
        if search:
            # поиск по номеру комнаты
            try:
                qs = qs.filter(room_number=int(search))
            except ValueError:
                pass

        # ---- pagination ----
        paginator = SmallPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = RoomShortSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data)

    @action(detail=False, methods=["get"], url_path="residents")
    def residents(self, request):
        hotel = admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        today = date.today()
        qs = CheckIn.objects.select_related("client", "room", "room__room_type", "booking", "staff").filter(
            room__hotel=hotel,
            date_check_in__lte=today,
            date_check_out__gte=today
        ).order_by("room__room_number")
        return Response(CheckInSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="checkin")
    def checkin(self, request):
        hotel = admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        staff_id = request.data.get("staff_id")
        if not staff_id:
            return Response({"detail": "staff_id is required (Staff is not linked to User)"}, status=400)

        staff = Staff.objects.filter(pk=staff_id).first()
        if not staff:
            return Response({"detail": "staff not found"}, status=404)

        ser = CheckInCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ch = ser.validated_data

        room = ch["room"]
        if room.hotel_id != hotel.id_hotel:
            return Response({"detail": "room is not in your hotel"}, status=400)

        if overlaps_checkin(CheckIn.objects.filter(room=room), ch["date_check_in"], ch["date_check_out"]).exists():
            return Response({"detail": "room is occupied in this period"}, status=400)

        booking = ch["booking"]
        booking.book_status = "Заселен"
        booking.save(update_fields=["book_status"])

        obj = CheckIn.objects.create(
            date_check_in=ch["date_check_in"],
            date_check_out=ch["date_check_out"],
            client=ch["client"],
            room=room,
            staff=staff,
            booking=booking
        )

        return Response(CheckInSerializer(obj).data, status=201)

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        hotel = admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        checkin = CheckIn.objects.select_related("room", "booking").filter(pk=pk, room__hotel=hotel).first()
        if not checkin:
            return Response({"detail": "checkin not found"}, status=404)

        d = parse_date(request.data.get("date_check_out")) if request.data.get("date_check_out") else date.today()
        if d < checkin.date_check_in:
            return Response({"detail": "date_check_out must be >= date_check_in"}, status=400)

        checkin.date_check_out = d
        checkin.save(update_fields=["date_check_out"])

        booking = checkin.booking
        booking.book_status = "Выселен"
        booking.save(update_fields=["book_status"])

        return Response(CheckInSerializer(checkin).data)

    @action(detail=False, methods=["post"], url_path="staff")
    def add_staff(self, request):
        ser = StaffSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        return Response(StaffSerializer(obj).data, status=201)

class AdminBookingsViewSet(viewsets.ViewSet):
    """
    /api/admin/bookings/  (GET)  — список броней по отелю админа (без Отменен/Выселен)
    /api/admin/bookings/{id}/ (PATCH) — изменить даты/статус (кроме Заселен/Выселен напрямую)
    /api/admin/bookings/{id}/checkin/ (POST) — заселить в конкретный room
    /api/admin/bookings/{id}/checkout/ (POST) — выселить и освободить room
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = SmallPagination

    def list(self, request):
        hotel = _admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        qs = (
            Booking.objects.select_related("client", "room_type", "hotel")
            .filter(hotel=hotel)
            .exclude(book_status__in=[CANCELLED, CHECKED_OUT])
            .order_by("-id_book")
        )

        # ---- filters ----
        status = request.query_params.get("status")
        if status:
            qs = qs.filter(book_status=status)

        type_id = request.query_params.get("type_id")
        if type_id:
            qs = qs.filter(room_type_id=type_id)

        # date overlap filter
        start = parse_date(request.query_params.get("start")) if request.query_params.get("start") else None
        end = parse_date(request.query_params.get("end")) if request.query_params.get("end") else None
        if start and end:
            qs = qs.filter(date_start__lte=end, date_end__gte=start)
        elif start:
            qs = qs.filter(date_end__gte=start)
        elif end:
            qs = qs.filter(date_start__lte=end)

        # client search
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(
                Q(client__name__icontains=q) |
                Q(client__surname__icontains=q) |
                Q(client__email__icontains=q)
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        ser = BookingAdminListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data)

    @transaction.atomic
    def partial_update(self, request, pk=None):
        hotel = _admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        booking = Booking.objects.select_related("hotel", "room_type").filter(pk=pk, hotel=hotel).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        if booking.book_status == "Заселен":
            return Response(
                {
                    "detail": "Нельзя менять заселённую бронь через редактирование. Используйте: /checkout/ или /change-room/."},
                status=400
            )
        old_start, old_end = booking.date_start, booking.date_end
        old_status = booking.book_status

        ser = BookingAdminUpdateSerializer(instance=booking, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("book_status", booking.book_status)

        # запрещаем напрямую ставить "Заселен" / "Выселен" — только через checkin/checkout,
        # иначе номер не назначится/не освободится
        if new_status in [CHECKED_IN, CHECKED_OUT]:
            return Response(
                {"detail": "Use /checkin/ for Заселен and /checkout/ for Выселен to keep room status consistent."},
                status=400,
            )

        booking = ser.save()

        # если поменяли даты — пересчитываем доступность по старому и новому диапазону
        if booking.date_start != old_start or booking.date_end != old_end:
            # проверка: достаточно ли свободных по типу на новый период
            # (по наличию комнат и активных броней)
            _recompute_availability(hotel, booking.room_type, min(old_start, booking.date_start), max(old_end, booking.date_end))

        # если поменяли статус на "Отменен" — пересчёт availability
        if old_status != booking.book_status:
            _recompute_availability(hotel, booking.room_type, booking.date_start, booking.date_end)

        return Response(BookingAdminListSerializer(booking, context={"request": request}).data)

    @transaction.atomic
    def checkin(self, request, pk=None):
        hotel = _admin_hotel(request)
        staff = _admin_staff(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)
        if not staff:
            return Response({"detail": "profile.staff is not set for this admin"}, status=400)

        booking = Booking.objects.select_related("hotel", "room_type", "client").filter(pk=pk, hotel=hotel).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        if booking.book_status in [CANCELLED, CHECKED_OUT]:
            return Response({"detail": "cannot check-in cancelled/checked-out booking"}, status=400)

        ser = BookingAdminCheckinSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        room_id = ser.validated_data["room_id"]

        room = RoomInHotel.objects.select_related("room_type").filter(id_number=room_id, hotel=hotel).first()
        if not room:
            return Response({"detail": "room not found in your hotel"}, status=404)

        if room.room_type_id != booking.room_type_id:
            return Response({"detail": "room type mismatch with booking.room_type"}, status=400)

        if not _room_is_free_for_period(room, booking.date_start, booking.date_end):
            return Response({"detail": "room is occupied in this period"}, status=400)

        # создаём checkin (если уже есть — можно запретить)
        if booking.checkins.exists():
            return Response({"detail": "booking already has a check-in record"}, status=400)

        checkin = CheckIn.objects.create(
            date_check_in=booking.date_start,
            date_check_out=booking.date_end,
            client=booking.client,
            room=room,
            staff=staff,
            booking=booking,
        )

        booking.book_status = "Заселен"
        booking.payed = booking.price  # ✅ оплатили полностью при заселении
        booking.save(update_fields=["book_status", "payed"])

        room.status = "Занят"
        room.cleaned = False
        room.save(update_fields=["status", "cleaned"])

        # пересчёт availability по типу на период
        _recompute_availability(hotel, booking.room_type, booking.date_start, booking.date_end)

        return Response({
            "booking": BookingAdminListSerializer(booking, context={"request": request}).data,
            "checkin": CheckInSerializer(checkin, context={"request": request}).data,
        }, status=201)

    @transaction.atomic
    def checkout(self, request, pk=None):
        hotel = _admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        booking = Booking.objects.select_related("hotel", "room_type").filter(pk=pk, hotel=hotel).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        if booking.book_status == CANCELLED:
            return Response({"detail": "cannot checkout cancelled booking"}, status=400)

        ch = booking.checkins.select_related("room").order_by("-id_check_in").first()
        if not ch:
            return Response({"detail": "no check-in record for this booking"}, status=400)

        ser = BookingAdminCheckoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d_out = ser.validated_data.get("date_check_out") or date.today()
        if d_out < ch.date_check_in:
            return Response({"detail": "date_check_out must be >= date_check_in"}, status=400)

        # обновляем checkin
        ch.date_check_out = d_out
        ch.save(update_fields=["date_check_out"])

        # освобождаем room
        room = ch.room
        room.status = "Свободен"
        room.cleaned = False
        room.save(update_fields=["status", "cleaned"])

        booking.book_status = "Выселен"
        booking.save(update_fields=["book_status"])

        # availability по типу на период брони
        _recompute_availability(hotel, booking.room_type, booking.date_start, booking.date_end)

        return Response({
            "booking": BookingAdminListSerializer(booking, context={"request": request}).data,
            "room": {"id_number": room.id_number, "room_number": room.room_number, "status": room.status, "cleaned": room.cleaned},
        })

    @transaction.atomic
    def change_room(self, request, pk=None):
        hotel = _admin_hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        booking = Booking.objects.select_related("hotel", "room_type").filter(pk=pk, hotel=hotel).first()
        if not booking:
            return Response({"detail": "booking not found"}, status=404)

        if booking.book_status != "Заселен":
            return Response({"detail": "Сменить номер можно только для статуса 'Заселен'."}, status=400)

        ch = booking.checkins.select_related("room", "room__room_type").order_by("-id_check_in").first()
        if not ch:
            return Response({"detail": "no check-in record for this booking"}, status=400)

        ser = BookingAdminChangeRoomSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new_room_id = ser.validated_data["room_id"]

        new_room = RoomInHotel.objects.select_related("room_type").filter(id_number=new_room_id, hotel=hotel).first()
        if not new_room:
            return Response({"detail": "room not found in your hotel"}, status=404)

        # 1) номер должен быть свободен на период
        if not _room_is_free_for_period(new_room, booking.date_start, booking.date_end):
            return Response({"detail": "room is occupied in this period"}, status=400)

        # 2) тип должен быть "такой же или выше"
        old_type = booking.room_type
        new_type = new_room.room_type

        # критерий "выше": по местам ИЛИ по цене (обычно так)
        if new_type.num_of_places < old_type.num_of_places:
            return Response({"detail": "Нельзя переселить в номер более низкого класса (меньше мест)."}, status=400)

        if new_type.base_price < old_type.base_price:
            return Response({"detail": "Нельзя переселить в номер более низкого класса (дешевле)."}, status=400)

        old_room = ch.room
        if old_room.id_number == new_room.id_number:
            return Response({"detail": "Это тот же самый номер."}, status=400)

        # 3) освобождаем старый номер
        old_room.status = "Свободен"
        old_room.cleaned = False
        old_room.save(update_fields=["status", "cleaned"])

        # 4) занимаем новый номер
        new_room.status = "Занят"
        new_room.cleaned = False
        new_room.save(update_fields=["status", "cleaned"])

        # 5) меняем номер в checkin
        ch.room = new_room
        ch.save(update_fields=["room"])

        # 6) если тип стал "выше" (или даже просто другой) — обновляем booking.room_type и цену
        if new_type.id_type != old_type.id_type:
            booking.room_type = new_type

            # вариант A: цена = base_price * дни
            days = (booking.date_end - booking.date_start).days + 1
            booking.price = new_type.base_price * max(days, 1)

            # ✅ по твоему требованию
            booking.payed = booking.price

            booking.save(update_fields=["room_type", "price", "payed"])
        else:
            # даже если тип тот же — по требованию “оплачено = цене”
            if booking.payed != booking.price:
                booking.payed = booking.price
                booking.save(update_fields=["payed"])

        # availability пересчитать по старому и новому типу (на всякий)
        _recompute_availability(hotel, old_type, booking.date_start, booking.date_end)
        _recompute_availability(hotel, booking.room_type, booking.date_start, booking.date_end)

        return Response({
            "detail": "Room changed",
            "booking": BookingAdminListSerializer(booking, context={"request": request}).data,
            "new_room": RoomShortSerializer(new_room, context={"request": request}).data,
        })

class AdminStaffViewSet(viewsets.ViewSet):
    """
    /api/admin/cleaners/                 GET (pagination)
    /api/admin/cleaners/<staff_id>/stats GET (start,end)
    /api/admin/cleaners/<staff_id>/fire  POST (deactivate user + delete token)
    /api/admin/cleanings/                GET (pagination + filters)
    /api/admin/cleanings/<id>/           PATCH (change status + update room.cleaned)
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = SmallPagination

    def _hotel(self, request):
        return admin_hotel(request)

    # ---------- CLEANERS ----------
    def list_cleaners(self, request):
        hotel = self._hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        qs = (
            Profile.objects
            .select_related("user", "staff", "hotel")
            .filter(role="cleaner", hotel=hotel)
            .exclude(staff__isnull=True)
            .order_by("staff__full_name")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)

        data = []
        for p in page:
            data.append({
                "staff_id": p.staff.id_staff,
                "full_name": p.staff.full_name,
                "username": p.user.username if p.user else None,
                "is_active": bool(p.user and p.user.is_active),
                "hotel_id": p.hotel.id_hotel,
                "hotel_name": p.hotel.name,
            })

        return paginator.get_paginated_response(CleanerListSerializer(data, many=True).data)

    def cleaner_stats(self, request, staff_id=None):
        hotel = self._hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        start = parse_date(request.query_params.get("start")) if request.query_params.get("start") else None
        end = parse_date(request.query_params.get("end")) if request.query_params.get("end") else None
        if not start or not end:
            return Response({"detail": "start and end are required (YYYY-MM-DD)"}, status=400)
        if end < start:
            return Response({"detail": "end must be >= start"}, status=400)

        cnt = CleaningTime.objects.filter(
            room__hotel=hotel,
            staff_id=staff_id,
            date__range=(start, end),
        ).count()

        return Response({"staff_id": int(staff_id), "start": str(start), "end": str(end), "cleanings_count": cnt})

    def fire_cleaner(self, request, staff_id=None):
        """
        "Уволить": человек больше не сможет зайти.
        Мы НЕ удаляем Staff (иначе сломаем историю из-за PROTECT в CleaningTime),
        а деактивируем Django user + удаляем токены.
        """
        hotel = self._hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        prof = Profile.objects.select_related("user", "staff").filter(
            role="cleaner", hotel=hotel, staff_id=staff_id
        ).first()
        if not prof or not prof.user:
            return Response({"detail": "cleaner not found"}, status=404)

        user = prof.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        Token.objects.filter(user=user).delete()

        return Response({"detail": "Cleaner fired (user deactivated).", "username": user.username, "staff_id": int(staff_id)})

    # ---------- CLEANINGS ----------
    def list_cleanings(self, request):
        hotel = self._hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        qs = (
            CleaningTime.objects
            .select_related("room", "room__room_type", "staff")
            .filter(room__hotel=hotel)
            .order_by("-date", "-cleaning_time")
        )

        # filters
        d = request.query_params.get("date")
        if d:
            dd = parse_date(d)
            if not dd:
                return Response({"detail": "invalid date"}, status=400)
            qs = qs.filter(date=dd)

        room_number = request.query_params.get("room_number")
        if room_number:
            try:
                qs = qs.filter(room__room_number=int(room_number))
            except ValueError:
                return Response({"detail": "room_number must be int"}, status=400)

        staff_id = request.query_params.get("staff_id")
        if staff_id:
            qs = qs.filter(staff_id=staff_id)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        ser = CleaningAdminSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data)

    def update_cleaning(self, request, pk=None):
        hotel = self._hotel(request)
        if not hotel:
            return Response({"detail": "profile.hotel is not set for admin"}, status=400)

        obj = CleaningTime.objects.select_related("room").filter(pk=pk, room__hotel=hotel).first()
        if not obj:
            return Response({"detail": "cleaning not found"}, status=404)

        ser = CleaningStatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data["cleaning_status"]
        obj.cleaning_status = new_status
        obj.save(update_fields=["cleaning_status"])

        # ✅ синхронизация с RoomInHotel.cleaned
        room = obj.room
        room.cleaned = True if new_status == "Убран" else False
        room.save(update_fields=["cleaned"])

        return Response(CleaningAdminSerializer(obj, context={"request": request}).data)
# --------------------
# Cleaner endpoints
# --------------------

class CleanerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsCleaner]

    @action(detail=False, methods=["get"], url_path="my-hotel")
    def my_hotel(self, request):
        hotel = request.user.profile.hotel
        if not hotel:
            return Response({"detail": "profile.hotel is not set for cleaner"}, status=400)
        return Response(HotelSerializer(hotel, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="rooms")
    def rooms(self, request):
        hotel = request.user.profile.hotel
        if not hotel:
            return Response({"detail": "profile.hotel is not set for cleaner"}, status=400)

        qs = (
            RoomInHotel.objects
            .filter(hotel=hotel)
            .filter(Q(cleaned=False) | Q(cleaned__isnull=True))
            .select_related("room_type")
            .order_by("room_number")
        )
        return Response(RoomShortSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="cleanings")
    def cleanings(self, request):
        hotel = request.user.profile.hotel
        if not hotel:
            return Response({"detail": "profile.hotel is not set for cleaner"}, status=400)

        d = parse_date(request.query_params.get("date")) or date.today()

        qs = (
            CleaningTime.objects
            .select_related("room", "staff", "room__room_type")
            .filter(room__hotel=hotel, date=d)
            .order_by("-cleaning_time")
        )

        return Response({
            "date": str(d),
            "items": CleaningSerializer(qs, many=True, context={"request": request}).data
        })

    @action(detail=False, methods=["post"], url_path="cleanings")
    def add_cleaning(self, request):
        hotel = request.user.profile.hotel
        if not hotel:
            return Response({"detail": "profile.hotel is not set for cleaner"}, status=400)

        staff = getattr(request.user.profile, "staff", None)
        if not staff:
            return Response({"detail": "profile.staff is not set for this user"}, status=400)

        ser = CleaningCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        room = ser.validated_data["room"]
        if room.hotel_id != hotel.id_hotel:
            return Response({"detail": "room is not in your hotel"}, status=400)

        cleaning_status = ser.validated_data["cleaning_status"]

        # ✅ создаём или обновляем запись уборки за день
        obj, created = CleaningTime.objects.update_or_create(
            room=room,
            date=ser.validated_data["date"],
            defaults={
                "staff": staff,
                "cleaning_time": ser.validated_data["cleaning_time"],
                "cleaning_status": cleaning_status,
            },
        )

        # ✅ обновляем room.cleaned
        room.cleaned = True if cleaning_status == "Убран" else False
        room.save(update_fields=["cleaned"])

        return Response(CleaningSerializer(obj, context={"request": request}).data, status=201 if created else 200)

    @action(detail=True, methods=["delete"], url_path="cleanings")
    def delete_cleaning(self, request, pk=None):
        hotel = request.user.profile.hotel
        if not hotel:
            return Response({"detail": "profile.hotel is not set for cleaner"}, status=400)

        obj = CleaningTime.objects.select_related("room").filter(pk=pk, room__hotel=hotel).first()
        if not obj:
            return Response({"detail": "cleaning not found"}, status=404)

        room = obj.room
        obj.delete()

        # ✅ раз записи уборки больше нет — считаем, что не убрано
        room.cleaned = False
        room.save(update_fields=["cleaned"])

        return Response(status=204)
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework.authtoken.models import Token

from .models import Profile, Hotel, Staff, ContractNumber, Client

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def staff_register(request):
    code = request.data.get("code")
    if code != getattr(settings, "STAFF_REGISTRATION_CODE", "staff-2026"):
        return Response({"detail": "Неверный код персонала"}, status=400)

    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email") or ""
    role = request.data.get("role")  # "cleaner" | "admin"
    hotel_id = request.data.get("hotel_id")
    full_name = request.data.get("full_name") or username

    if not username or not password or not hotel_id:
        return Response({"detail": "username, password, hotel_id обязательны"}, status=400)

    if role not in ("cleaner", "admin"):
        return Response({"detail": "role должен быть cleaner или admin"}, status=400)

    hotel = Hotel.objects.filter(id_hotel=hotel_id).first()
    if not hotel:
        return Response({"detail": "hotel not found"}, status=404)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "username уже занят"}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)

    next_contract = (ContractNumber.objects.aggregate(m=Max("contract_number"))["m"] or 0) + 1
    today = date.today()
    contract = ContractNumber.objects.create(
        contract_number=next_contract,
        beginning_of_contract=today,
        end_of_contract=today + timedelta(days=365),
        number_of_job_days=20,
        type_of_contract="Постоянный",
        conditions="auto-created",
    )

    job_title = "Уборщик" if role == "cleaner" else "Администратор"
    staff = Staff.objects.create(contract=contract, full_name=full_name[:150], job_title=job_title)

    profile = user.profile
    profile.role = Profile.Role.CLEANER if role == "cleaner" else Profile.Role.ADMIN
    profile.hotel = hotel
    profile.staff = staff
    profile.client = None
    profile.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"auth_token": token.key}, status=201)

@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def client_register(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email") or ""
    if not username or not password:
        return Response({"detail": "username и password обязательны"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"detail": "username уже занят"}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)

    # создаём Client “минимально”, потом можно расширить форму
    client = Client.objects.create(
        name=username[:30],
        surname="",
        fathers_name="",
        home_adress="",
        mobile_number="",
        email=email or f"{username}@example.com",
    )

    profile = user.profile
    profile.role = Profile.Role.CLIENT
    profile.client = client
    profile.hotel = None
    profile.staff = None
    profile.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"auth_token": token.key}, status=201)
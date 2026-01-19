from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Q
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from django.views.generic import ListView

from .forms import CustomUserCreationForm, ReservationCreateForm, ReviewForm, ReservationUpdateForm
from .models import Hotel, HotelRoomType, Reservation, Review


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")



class HotelListView(ListView):
    model = Hotel
    template_name = "hotel_list.html"
    context_object_name = "hotels"
    paginate_by = 10

    def get_queryset(self):
        qs = Hotel.objects.all().order_by("name")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(address__icontains=q) |
                Q(description__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        ctx["q"] = q
        ctx["last_q"] = f"?q={q}" if q else ""
        return ctx

def hotel_guests_last_month(request, hotel_id: int):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    start = (timezone.now() - timedelta(days=30)).date()
    end = timezone.now().date()

    reservations = (
        Reservation.objects
        .filter(
            hotel_room_type__hotel=hotel,
            status__in=[Reservation.Status.CHECKED_IN, Reservation.Status.CHECKED_OUT],
        )
        # пересечение интервалов: [check_in, check_out) с [start, end]
        .filter(check_in__lte=end, check_out__gte=start)
        .select_related("user", "hotel_room_type__room_type")
        .order_by("-check_in")
    )

    return render(
        request,
        "hotel_guests_last_month.html",
        {
            "hotel": hotel,
            "reservations": reservations,
            "start": start,
            "end": end,
        },
    )

def hotel_detail(request, hotel_id: int):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    room_types = (
        HotelRoomType.objects.filter(hotel=hotel)
        .select_related("room_type", "hotel")
        .prefetch_related("room_type__amenities")
        .order_by("price_per_night", "room_type__title")
    )

    return render(request, "hotel_detail.html", {"hotel": hotel, "room_types": room_types})

def available_units_for_dates(hrt, check_in, check_out) -> int:
    active_count = Reservation.objects.filter(
        hotel_room_type=hrt,
        status__in=[Reservation.Status.BOOKED, Reservation.Status.CHECKED_IN],
    ).filter(
        Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
    ).count()
    return max(hrt.total_units - active_count, 0)

def room_detail(request, room_id: int):
    """
    Room page (in new architecture):
    `room_id` is actually HotelRoomType.id
    Shows: availability, reviews, and allows reserve/cancel/review for logged-in users.
    """
    hrt = get_object_or_404(
        HotelRoomType.objects.select_related("hotel", "room_type"),
        pk=room_id,
    )

    reviews = (
        Review.objects.filter(hotel_room_type=hrt)
        .select_related("author")
        .order_by("-created_at")
    )

    reservation_form = ReservationCreateForm()
    review_form = ReviewForm()
    error_message = None

    my_active_reservations = []
    if request.user.is_authenticated:
        my_active_reservations = list(
            Reservation.objects.filter(user=request.user, hotel_room_type=hrt)
            .exclude(status__in=[Reservation.Status.CANCELED, Reservation.Status.CHECKED_OUT])
            .order_by("-created_at")
        )

    if request.method == "POST":
        action = request.POST.get("action")

        if not request.user.is_authenticated:
            return redirect("/accounts/login/?next=" + request.path)

        if action == "reserve":
            reservation_form = ReservationCreateForm(request.POST)
            if reservation_form.is_valid():
                check_in = reservation_form.cleaned_data["check_in"]
                check_out = reservation_form.cleaned_data["check_out"]

                with transaction.atomic():
                    hrt_locked = HotelRoomType.objects.select_for_update().get(pk=hrt.pk)
                    available = available_units_for_dates(hrt_locked, check_in, check_out)

                    if hrt_locked.total_units <= 0:
                        error_message = "No units configured for this room type."
                    elif available <= 0:
                        error_message = "No available rooms for the selected dates."
                    else:
                        Reservation.objects.create(
                            user=request.user,
                            hotel_room_type=hrt_locked,
                            check_in=check_in,
                            check_out=check_out,
                            status=Reservation.Status.BOOKED,
                        )
                        return redirect(request.path)

        elif action == "cancel_reservation":
            reservation_id = request.POST.get("reservation_id")
            try:
                r = Reservation.objects.get(
                    pk=reservation_id,
                    user=request.user,
                    hotel_room_type=hrt
                )
                if r.status in [Reservation.Status.BOOKED, Reservation.Status.CHECKED_IN]:
                    r.status = Reservation.Status.CANCELED
                    r.save(update_fields=["status", "updated_at"])
                return redirect(request.path)
            except Reservation.DoesNotExist:
                raise Http404("Reservation not found")

        elif action == "add_review":
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.author = request.user
                review.hotel_room_type = hrt
                review.save()
                return redirect(request.path)

    return render(
        request,
        "room_detail.html",
        {
            "hrt": hrt,  # HotelRoomType объект
            "hotel": hrt.hotel,
            "room_type": hrt.room_type,

            "reviews": reviews,
            "reservation_form": reservation_form,
            "review_form": review_form,
            "my_active_reservations": my_active_reservations,
            "error_message": error_message,
        },
    )

def reservation_edit(request, reservation_id: int):
    if not request.user.is_authenticated:
        return redirect("/accounts/login/?next=" + request.path)

    reservation = get_object_or_404(
        Reservation.objects.select_related("hotel_room_type", "hotel_room_type__hotel", "hotel_room_type__room_type"),
        pk=reservation_id,
        user=request.user,
    )

    # обычно разрешаем менять даты только пока бронь BOOKED
    if reservation.status != Reservation.Status.BOOKED:
        return render(
            request,
            "reservation_edit.html",
            {
                "form": None,
                "reservation": reservation,
                "error_message": "You can edit dates only for BOOKED reservations.",
            },
        )

    form = ReservationUpdateForm(request.POST or None, instance=reservation)
    error_message = None

    if request.method == "POST" and form.is_valid():
        check_in = form.cleaned_data["check_in"]
        check_out = form.cleaned_data["check_out"]
        hrt = reservation.hotel_room_type

        # считаем пересечения по датам (исключая текущую бронь)
        overlap_count = Reservation.objects.filter(
            hotel_room_type=hrt,
            status__in=[Reservation.Status.BOOKED, Reservation.Status.CHECKED_IN],
        ).exclude(
            pk=reservation.pk
        ).filter(
            Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
        ).count()

        if hrt.total_units <= 0:
            error_message = "No units configured for this room type."
        elif overlap_count >= hrt.total_units:
            error_message = "No available rooms for the selected dates."
        else:
            form.save()
            return redirect(f"/rooms/{hrt.pk}/")

    return render(
        request,
        "reservation_edit.html",
        {
            "form": form,
            "reservation": reservation,
            "error_message": error_message,
        },
    )
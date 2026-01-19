from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView

from .models import Car
from .forms import CustomUserCreationForm

User = get_user_model()


def owner_detail(request, owner_id: int):
    try:
        owner = User.objects.get(pk=owner_id)
    except User.DoesNotExist:
        raise Http404("User does not exist")
    return render(request, "owner.html", {"owner": owner})


def owners_list(request):
    owners = User.objects.all().order_by("last_name", "first_name", "username")
    return render(request, "owners_list.html", {"owners": owners})


def owner_create(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("/owners/")
    return render(request, "owner_create.html", {"form": form})


class CarListView(ListView):
    model = Car
    template_name = "car_list.html"
    context_object_name = "cars"


class CarDetailView(DetailView):
    model = Car
    template_name = "car_detail.html"
    context_object_name = "car"


class CarUpdateView(UpdateView):
    model = Car
    fields = ["plate_number", "brand", "model", "color"]
    template_name = "car_form.html"
    success_url = "/cars/"


class CarCreateView(CreateView):
    model = Car
    fields = ["plate_number", "brand", "model", "color"]
    template_name = "car_create.html"
    success_url = "/cars/"


class CarDeleteView(DeleteView):
    model = Car
    template_name = "car_confirm_delete.html"
    success_url = "/cars/"
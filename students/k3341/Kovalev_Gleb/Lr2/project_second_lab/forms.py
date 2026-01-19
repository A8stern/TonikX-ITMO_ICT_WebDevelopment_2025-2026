from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Reservation, Review

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )


class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ("check_in", "check_out")
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")

        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError("Check-out date must be after check-in date")

        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("stay_from", "stay_to", "rating", "text")
        widgets = {
            "stay_from": forms.DateInput(attrs={"type": "date"}),
            "stay_to": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        stay_from = cleaned.get("stay_from")
        stay_to = cleaned.get("stay_to")

        if stay_from and stay_to and stay_from >= stay_to:
            raise forms.ValidationError("Stay end date must be after stay start date")

        return cleaned

class ReservationUpdateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ("check_in", "check_out")
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        if check_in and check_out and check_in >= check_out:
            raise forms.ValidationError("Check-out date must be after check-in date")
        return cleaned
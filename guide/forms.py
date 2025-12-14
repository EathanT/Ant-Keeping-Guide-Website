from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    NuptialFlight,
    ForumThread,
    ForumPost,
    SpeciesSuggestion,
    Profile,
    Species,
)

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "display_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, created = Profile.objects.get_or_create(user=user)
            display_name = self.cleaned_data.get("display_name")
            if display_name:
                profile.display_name = display_name
                profile.save()
        return user


class SpeciesFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    difficulty = forms.ChoiceField(
        choices=[("", "Any")] + list(Species.DIFFICULTY_CHOICES),
        required=False,
    )
    region = forms.ChoiceField(
        choices=[("", "Any")] + list(Species.REGION_CHOICES),
        required=False,
    )
    founding_mode = forms.ChoiceField(
        choices=[("", "Any")] + list(Species.FOUNDING_MODE_CHOICES),
        required=False,
    )
    diapause = forms.ChoiceField(
        choices=[("", "Any")] + list(Species.DIAPAUSE_CHOICES),
        required=False,
    )


class NuptialFlightForm(forms.ModelForm):
    class Meta:
        model = NuptialFlight
        fields = ["species", "location_name", "latitude", "longitude", "date", "region", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class ForumThreadForm(forms.ModelForm):
    class Meta:
        model = ForumThread
        fields = ["title", "species"]


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }


class SpeciesSuggestionForm(forms.ModelForm):
    class Meta:
        model = SpeciesSuggestion
        fields = [
            "species",
            "proposed_genus",
            "proposed_species",
            "proposed_common_name",
            "care_notes",
            "reason",
        ]
        widgets = {
            "care_notes": forms.Textarea(attrs={"rows": 6}),
            "reason": forms.Textarea(attrs={"rows": 4}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "favorite_region", "receive_email_updates"]

from django import forms

from places.models import Place

KRAKOW_BBOX = {"lat": (49.9, 50.2), "lng": (19.7, 20.2)}


class PlaceSubmissionForm(forms.ModelForm[Place]):
    class Meta:
        model = Place
        fields = ["name", "address", "latitude", "longitude", "food_types", "instagram_url"]
        widgets = {"food_types": forms.CheckboxSelectMultiple}

    def clean_latitude(self) -> float:
        value: float = self.cleaned_data["latitude"]
        if not KRAKOW_BBOX["lat"][0] <= value <= KRAKOW_BBOX["lat"][1]:
            raise forms.ValidationError("Place must be in Kraków.")
        return value

    def clean_longitude(self) -> float:
        value: float = self.cleaned_data["longitude"]
        if not KRAKOW_BBOX["lng"][0] <= value <= KRAKOW_BBOX["lng"][1]:
            raise forms.ValidationError("Place must be in Kraków.")
        return value

    def clean_instagram_url(self) -> str:
        url: str = self.cleaned_data["instagram_url"]
        if url and not url.startswith(("http://", "https://")):
            raise forms.ValidationError("Enter an http(s) link.")
        return url

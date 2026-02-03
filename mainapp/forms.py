from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class WeightGainForm(forms.Form):
    height = forms.FloatField(label="Height (cm)")
    current_weight = forms.FloatField(label="Current Weight (kg)")
    target_gain = forms.FloatField(label="Weight to Gain (kg)")
    duration = forms.IntegerField(label="Duration (days)")


class WeightLossForm(forms.Form):
    current_weight = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    target_weight = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    duration_days = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    diet_type = forms.ChoiceField(
        choices=[('veg', 'Vegetarian'), ('nonveg', 'Non-Veg'), ('vegan', 'Vegan')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )




class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True)
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        required=True
    )
    diet_preference = forms.ChoiceField(
        choices=[('veg', 'Vegetarian'), ('nonveg', 'Non-Vegetarian'), ('vegan', 'Vegan')],
        required=True
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'age',
            'gender',
            'diet_preference',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        # Save User only; profile will be created by signal
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = True  # you can change to False if email verification is needed

        if commit:
            user.save()
        return user

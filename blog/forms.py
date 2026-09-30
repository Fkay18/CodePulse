from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Blog


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['unit', 'title', 'slug', 'content', 'image_url', 'author']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'image_url': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ClientSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user

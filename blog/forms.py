from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Blog, Project, UserProfile


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


class UserProfileForm(forms.ModelForm):
    max_profile_picture_size = 5 * 1024 * 1024
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'autocomplete': 'email',
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user or (self.instance.user if self.instance.pk else None)
        if self.user:
            self.initial['email'] = self.user.email

    class Meta:
        model = UserProfile
        fields = (
            'profile_picture',
            'display_name',
            'bio',
            'phone_number',
            'instagram_url',
            'linkedin_url',
            'x_url',
            'show_email',
            'receive_newsletter',
        )
        labels = {
            'profile_picture': 'Profile photo',
            'display_name': 'Display name',
            'bio': 'Biography',
            'phone_number': 'Phone number',
            'instagram_url': 'Instagram',
            'linkedin_url': 'LinkedIn',
            'x_url': 'X',
            'show_email': 'Show my email on my public profile',
            'receive_newsletter': 'Email me CodePulse news and updates',
        }
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'profile-picture-input',
                'accept': 'image/*',
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'nickname',
                'maxlength': 150,
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'maxlength': 500,
            }),
            'phone_number': forms.TelInput(attrs={
                'class': 'form-control',
                'autocomplete': 'tel',
            }),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/you'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/you'}),
            'x_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/you'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receive_newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        existing_users = get_user_model().objects.filter(email__iexact=email)
        if self.user:
            existing_users = existing_users.exclude(pk=self.user.pk)
        if existing_users.exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture and picture.size > self.max_profile_picture_size:
            raise ValidationError('Choose an image smaller than 5 MB.')
        return picture

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit and self.user:
            email = self.cleaned_data['email']
            if self.user.email != email:
                self.user.email = email
                self.user.save(update_fields=['email'])
        return profile


class ProjectForm(forms.ModelForm):
    max_image_size = 5 * 1024 * 1024

    class Meta:
        model = Project
        fields = ('name', 'description', 'technologies', 'github_url', 'live_url', 'image')
        labels = {
            'name': 'Project name',
            'description': 'Description',
            'technologies': 'Technologies',
            'github_url': 'GitHub URL',
            'live_url': 'Live or demo URL',
            'image': 'Project image',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 120}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'maxlength': 1000}),
            'technologies': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 300,
                'placeholder': 'Python, Django, DRF, MySQL',
            }),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/you/project'}),
            'live_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://your-project.example'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > self.max_image_size:
            raise ValidationError('Choose a project image smaller than 5 MB.')
        return image

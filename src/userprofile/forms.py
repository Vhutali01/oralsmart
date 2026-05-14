from django import forms
from django.contrib.auth.models import User
from .models import Profile

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic']
        widgets = {
            'profile_pic': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

class UserNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            })
        }

class ProfileContactForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['tel', 'address']
        widgets = {
            'tel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address'
            })
        }
        labels = {
            'tel': 'Phone',
            'address': 'Address'
        }

class ProfileProfessionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profession']
        widgets = {
            'profession': forms.Select(attrs={
                'class': 'form-select'
            })
        }

class ProfileEmailForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            })
        }

class ProfilePhoneForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['tel']
        widgets = {
            'tel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            })
        }
        labels = {
            'tel': 'Phone'
        }

class ProfileAddressForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['address']
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Address'
            })
        }
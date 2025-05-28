"""
Forms for the Content Moderation Dashboard
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name'
    }))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class TextModerationForm(forms.Form):
    """Form for testing text moderation"""
    text_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter text content to moderate...',
            'required': True
        }),
        label='Text Content',
        help_text='Enter the text you want to moderate for inappropriate content.'
    )
    user_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional user ID for tracking'
        }),
        label='User ID (Optional)',
        help_text='Optional user identifier for tracking purposes.'
    )


class ImageModerationForm(forms.Form):
    """Form for testing image moderation"""
    image_file = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'required': True
        }),
        label='Image File',
        help_text='Upload an image file to moderate (JPEG, PNG, GIF, BMP, WEBP supported, max 10MB).'
    )
    user_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional user ID for tracking'
        }),
        label='User ID (Optional)',
        help_text='Optional user identifier for tracking purposes.'
    )

    def clean_image_file(self):
        image = self.cleaned_data.get('image_file')
        if image:
            # Check file size (10MB limit)
            if image.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError('Image file size cannot exceed 10MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
            if image.content_type not in allowed_types:
                raise forms.ValidationError('Unsupported file type. Please upload JPEG, PNG, GIF, BMP, or WEBP images.')
        
        return image

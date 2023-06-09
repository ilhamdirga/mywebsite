from django import forms
from .models import Post, IpCamera

class PostForm(forms.ModelForm):
    picture = forms.ImageField(label="Picture", widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Post
        fields = [
            'name',
            'fullName',
            'picture'
        ]
    
        widgets = {
            'name': forms.TextInput(
                attrs = {
                    'class': 'form-control',
                    'placeholder': 'Fill with one word and this field can\'t be updated'
                }
            ),
            'fullName': forms.TextInput(
                attrs = {
                    'class': 'form-control',
                    'placeholder': 'Fill with your full name'
                },
            ),
        }

class IpCameraForm(forms.ModelForm):
    class Meta:
        model = IpCamera
        fields = [
            'name',
            'ip_camera'
        ]

        widgets = {
            'name': forms.TextInput(
                attrs = {
                    'class': 'form-control',
                    'placeholder': 'Fill with your name Ip Camera'
                }
            ),
            'ip_camera': forms.TextInput(
                attrs = {
                    'class': 'form-control',
                    'placeholder': 'Fill with your IP Camera Address'
                },
            ),
        }

        
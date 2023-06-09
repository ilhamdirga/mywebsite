from django import forms
from .models import Camera, ListCamera

# Form untuk user menambahkan Camera
class AddCameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = [
            'name',
            'description',
            'ip_camera'
        ]

        widgets = {
            'name': forms.TextInput(
                attrs= {
                    'class': 'form-control',
                    'placeholder': 'This field can not be modified'
                }
            ),
            'description': forms.TextInput(
                attrs= {
                    'class': 'form-control',
                    'placeholder': 'Fill the description'
                }
            ),
            'ip_camera': forms.TextInput(
                attrs= {
                    'class': 'form-control',
                    'placeholder': 'If no ip camera, fill with \'-\', \'None\', or \'none\''
                }
            )
        }


# Untuk couting via POST
class ListCameraForm(forms.Form):
    name = forms.ModelChoiceField(queryset=Camera.objects.all(), label='Select Memory Tray',widget=forms.Select(attrs={'class': 'form-select'}))
    picture = forms.ImageField(label="Image", widget=forms.FileInput(attrs={'class': 'form-control'}))

    TYPE_TRAY = (
    ('', '---------'),
    ('ssd', 'SSD'),
    ('hdd', 'HDD')
    )

    type_tray = forms.ChoiceField(choices=TYPE_TRAY, label='Tray Type', widget=forms.Select(attrs={'class':'form-select'}), initial='')
    class Meta:
        model = ListCamera
        fields = [
            'name',
            'picture',
            'type_tray'
        ]

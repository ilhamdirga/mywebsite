from django import forms
from .models import Camera, Gallery
from datetime import date
from django.utils import timezone
from calendar import monthrange

import django_filters

# Untuk memfilter list camera
class CameraFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        label="Name",
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Camera
        fields = [
            'name'
        ]

# Untuk memnfilter list photo di Gallery berdasarkan nama Camera dalam bentuk choice
class GalleryFilter(django_filters.FilterSet):
    name = django_filters.ModelChoiceFilter(
        label="Trash-can",
        queryset=Camera.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    CHOICES = (
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
    )

    timestamp= django_filters.ChoiceFilter(
        label='Period',
        choices=CHOICES,
        method='filter_detected',
        initial='today',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def filter_detected(self, queryset, name, value):
        today = date.today()
        if value == 'today':
            return queryset.filter(timestamp__date=today)
        elif value == 'this_week':
            start_of_week = today - timezone.timedelta(days=today.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=7)
            return queryset.filter(timestamp__date__range=[start_of_week, end_of_week])
        elif value == 'this_month':
            start_of_month = today.replace(day=1)
            end_of_month = start_of_month.replace(day=monthrange(start_of_month.year, start_of_month.month)[1])
            return queryset.filter(timestamp__date__range=[start_of_month, end_of_month])
        else:
            return queryset
        
    start_date = django_filters.DateFilter(field_name='detected_day',
                                           lookup_expr='gte',
                                            label='Range',
                                            widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'MM/DD/YY'}))
    end_date = django_filters.DateFilter(field_name='detected_day',
                                         lookup_expr='lte',
                                          label='-',
                                          widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'MM/DD/YY'}))

    class Meta:
        model = Gallery
        fields = [
            'name',
            'timestamp' 
            ]

    
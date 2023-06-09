from django import forms
from .models import Post, DetectedFace
from calendar import monthrange
from django.utils import timezone
from datetime import date, datetime
from django.contrib import messages
from django.core.exceptions import ValidationError


import django_filters

class DatabaseFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date_created', lookup_expr='gte', label='Start')
    end_date = django_filters.DateFilter(field_name='date_created', lookup_expr='lte', label='End')
    name = django_filters.CharFilter(
        lookup_expr='icontains', 
        label='Name',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Post
        fields = [
            'name'
        ]


class DetectedFilter(django_filters.FilterSet):
    CHOICES = (
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
    )

    name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Name',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    detected_time= django_filters.ChoiceFilter(
        label='Period',
        choices=CHOICES,
        method='filter_detected',
        initial='today',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def filter_detected(self, queryset, name, value):
        today = date.today()
        if value == 'today':
            return queryset.filter(detected_time__date=today)
        elif value == 'this_week':
            start_of_week = today - timezone.timedelta(days=today.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=7)
            return queryset.filter(detected_time__date__range=[start_of_week, end_of_week])
        elif value == 'this_month':
            start_of_month = today.replace(day=1)
            end_of_month = start_of_month.replace(day=monthrange(start_of_month.year, start_of_month.month)[1])
            return queryset.filter(detected_time__date__range=[start_of_month, end_of_month])
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
        model = DetectedFace
        fields = [
            'name',
            'detected_time',
        ]

    

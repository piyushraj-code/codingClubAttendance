from django import forms
from .models import ClubActivity, AttendanceRecord


class ClubActivityForm(forms.ModelForm):
    """Form to create or edit club activities."""
    class Meta:
        model = ClubActivity
        fields = ['title', 'activity_type', 'date', 'time', 'venue', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. AI & ML Hands-on Workshop'}),
            'activity_type': forms.Select(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'venue': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Auditorium / Computer Lab 3'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Overview of this session'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

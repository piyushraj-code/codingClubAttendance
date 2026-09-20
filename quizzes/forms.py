from django import forms
from .models import DailyQuiz, QuizOption


class DailyQuizForm(forms.ModelForm):
    """
    Form to create or update a Daily Quiz with question and explanation.
    """
    class Meta:
        model = DailyQuiz
        fields = ['date', 'title', 'question', 'explanation', 'points', 'is_active']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Python Data Structures Poll'}),
            'question': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Enter the question text here...'}),
            'explanation': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Explain why the correct answer is correct. This is shown to students after they submit their vote.'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class QuizOptionInlineForm(forms.ModelForm):
    class Meta:
        model = QuizOption
        fields = ['option_text', 'is_correct']
        widgets = {
            'option_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Option text'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

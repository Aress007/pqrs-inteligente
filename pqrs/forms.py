from django import forms
from django.contrib.auth.models import User
from .models import RespuestaPqrs

class RespuestaForm(forms.ModelForm):
    class Meta:
        model = RespuestaPqrs
        fields = ['texto_respuesta', 'archivo']
        widgets = {
            'texto_respuesta': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Escribe tu respuesta...'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }
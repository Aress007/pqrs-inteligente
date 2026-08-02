from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from empresas.models import Empresa, Plan

# Formulario de registro unificado (existente)
class RegistroUnificadoForm(forms.Form):
    username = forms.CharField(max_length=150, label="Nombre de usuario", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono", widget=forms.TextInput(attrs={'class': 'form-control'}))
    es_empresa = forms.BooleanField(required=False, label="Registrarse como empresa", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    nombre_empresa = forms.CharField(max_length=150, required=False, label="Nombre de la empresa", widget=forms.TextInput(attrs={'class': 'form-control'}))
    nit = forms.CharField(max_length=20, required=False, label="NIT", widget=forms.TextInput(attrs={'class': 'form-control'}))
    direccion = forms.CharField(max_length=255, required=False, label="Dirección", widget=forms.TextInput(attrs={'class': 'form-control'}))
    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), required=False, label="Plan de suscripción", widget=forms.Select(attrs={'class': 'form-select'}))

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado")
        return username

    def clean(self):
        cleaned_data = super().clean()
        es_empresa = cleaned_data.get('es_empresa')
        if es_empresa:
            if not cleaned_data.get('nombre_empresa'):
                self.add_error('nombre_empresa', 'El nombre de la empresa es obligatorio')
            if not cleaned_data.get('nit'):
                self.add_error('nit', 'El NIT es obligatorio')
            if not cleaned_data.get('plan'):
                self.add_error('plan', 'Debe seleccionar un plan')
            nit = cleaned_data.get('nit')
            if nit and Empresa.objects.filter(nit=nit).exists():
                self.add_error('nit', 'Ya existe una empresa con este NIT')
        return cleaned_data

# Formulario para editar perfil (datos básicos)
class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
        }
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que el username sea obligatorio
        self.fields['username'].required = True
        self.fields['email'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado")
        return email

# Formulario para cambiar teléfono (desde el perfil)
class EditarTelefonoForm(forms.Form):
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono", widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))

# Formulario para cambiar contraseña (con validación de la actual)
class CambiarPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(label="Contraseña actual", widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'}))
    new_password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'}))
    new_password2 = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control form-control-lg'})
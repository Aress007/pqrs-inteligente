from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from empresas.models import Empresa, Plan

# ============================================================
# REGISTRO UNIFICADO (PLACEHOLDERS AGREGADOS)
# ============================================================
class RegistroUnificadoForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu usuario'
        })
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    telefono = forms.CharField(
        max_length=15,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '300 000 0000'
        })
    )
    
    nombres = forms.CharField(
        max_length=50,
        required=False,
        label="Nombres",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tus nombres'
        })
    )
    apellidos = forms.CharField(
        max_length=50,
        required=False,
        label="Apellidos",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tus apellidos'
        })
    )
    cedula = forms.CharField(
        max_length=20,
        required=False,
        label="Cédula",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de cédula'
        })
    )
    
    # ==========================================================
    # CAMPOS DE EMPRESA
    # ==========================================================
    es_empresa = forms.BooleanField(
        required=False,
        label="Registrarse como empresa",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    nombre_empresa = forms.CharField(
        max_length=150,
        required=False,
        label="Nombre de la empresa",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de tu empresa'
        })
    )
    nit = forms.CharField(
        max_length=20,
        required=False,
        label="NIT",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123.456.789-0'
        })
    )
    direccion = forms.CharField(
        max_length=255,
        required=False,
        label="Dirección",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Calle 123 #45-67'
        })
    )
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.all(),
        required=False,
        label="Plan de suscripción",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

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


# ============================================================
# EDITAR PERFIL
# ============================================================
class EditarPerfilForm(forms.ModelForm):
    nombres = forms.CharField(
        max_length=50,
        required=False,
        label="Nombres",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ingresa tus nombres'})
    )
    apellidos = forms.CharField(
        max_length=50,
        required=False,
        label="Apellidos",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Ingresa tus apellidos'})
    )
    cedula = forms.CharField(
        max_length=20,
        required=False,
        label="Cédula",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Número de cédula'})
    )
    telefono = forms.CharField(
        max_length=15,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '300 000 0000'})
    )
    foto = forms.ImageField(
        required=False,
        label="Foto de perfil",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    logo = forms.ImageField(
        required=False,
        label="Logo de la empresa",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'perfil'):
            perfil = self.instance.perfil
            self.fields['nombres'].initial = perfil.nombres if perfil.nombres else ''
            self.fields['apellidos'].initial = perfil.apellidos if perfil.apellidos else ''
            self.fields['cedula'].initial = perfil.cedula if perfil.cedula else ''
            self.fields['telefono'].initial = perfil.telefono if perfil.telefono else ''

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto:
            ext = foto.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                raise forms.ValidationError("Formato no permitido. Usa JPG, PNG o GIF.")
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede superar los 5 MB.")
        return foto

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            ext = logo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                raise forms.ValidationError("Formato no permitido. Usa JPG, PNG o GIF.")
            if logo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede superar los 5 MB.")
        return logo

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            perfil = user.perfil
            perfil.nombres = self.cleaned_data.get('nombres')
            perfil.apellidos = self.cleaned_data.get('apellidos')
            perfil.cedula = self.cleaned_data.get('cedula')
            perfil.telefono = self.cleaned_data.get('telefono')
            if self.cleaned_data.get('foto'):
                perfil.foto = self.cleaned_data['foto']
            if self.cleaned_data.get('logo'):
                perfil.logo = self.cleaned_data['logo']
            perfil.save()
        return user


# ============================================================
# CAMBIAR CONTRASEÑA
# ============================================================
class CambiarPasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': '••••••••'})
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nueva contraseña'})
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Confirma la nueva contraseña'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control form-control-lg'})
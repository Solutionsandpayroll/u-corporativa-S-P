# forms.py
from django import forms
from .models import Usuario


#==========================================================
# FORMULARIOS PARA GESTIÓN DE USUARIOS
#==========================================================

class CrearUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'rol']
        labels = {'nombre_completo': 'Nombre completo', 'rol': 'Rol'}
        widgets = {'rol': forms.Select(choices=Usuario.ROL_CHOICES)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre_completo'].help_text = 'Se guardará en mayúsculas y se usará como nombre de usuario.'

    def clean_nombre_completo(self):
        nombre = self.cleaned_data['nombre_completo']
        return nombre.upper()  # Convertir a mayúsculas

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data['nombre_completo'].upper()
        usuario.set_password('Empleado2026*')
        if commit:
            usuario.save()
        return usuario


class EditarUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'rol', 'estado']
        labels = {'nombre_completo': 'Nombre completo', 'rol': 'Rol', 'estado': 'Estado'}
        widgets = {'rol': forms.Select(choices=Usuario.ROL_CHOICES), 'estado': forms.Select(choices=Usuario.ESTADO_CHOICES)}

    def clean_nombre_completo(self):
        nombre = self.cleaned_data['nombre_completo']
        return nombre.upper()

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data['nombre_completo'].upper()
        if commit:
            usuario.save()
        return usuario
    
#============================================================================
# FORMULARIOS PARA LA ACTUALIZACION DE LA CONTRASEÑA SI SE OLVIDA 
#============================================================================

class RecuperacionForm(forms.Form):
    correo = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@dominio.com'})
    )

    def clean_correo(self):
        correo = self.cleaned_data['correo']
        if not Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError('No existe un usuario con ese correo electrónico.')
        return correo

class VerificarCodigoForm(forms.Form):
    codigo = forms.CharField(
        label='Código de verificación',
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000000'})
    )

class ResetPasswordForm(forms.Form):
    nueva_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'id': 'nuevaPassword', 'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'id': 'confirmPassword', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('nueva_password')
        confirm = cleaned_data.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError('Las contraseñas no coinciden.')

        if pwd:
            if len(pwd) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
            if not any(c.isupper() for c in pwd):
                raise forms.ValidationError('Debe contener al menos una mayúscula.')
            if not any(c.isdigit() for c in pwd):
                raise forms.ValidationError('Debe contener al menos un número.')
            if not any(c in '!@#$%^&*(),.?":{}|<>' for c in pwd):
                raise forms.ValidationError('Debe contener al menos un carácter especial.')
        return cleaned_data
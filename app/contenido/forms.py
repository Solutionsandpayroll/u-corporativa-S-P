# =========================================================
# FORMS
# =========================================================

from django import forms
from .models import *
from .utils import *


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'editar-input',
                'placeholder': 'Título de la noticia'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'editar-textarea',
                'placeholder': 'Descripción opcional de la noticia',
                'rows': 5
            }),
        }

class ContenidoForm(forms.ModelForm):
    class Meta:
        model = Contenido
        fields = ['tipo_con', 'url_recurso']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url_recurso'].required = False  # ← ahora es opcional


class CursoForm(forms.ModelForm):
    """Formulario base para cursos."""

    # Campo personalizado con opciones fijas
    estado = forms.ChoiceField(
        choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')],
        widget=forms.Select(attrs={
            'class': 'form-input-modern',
            'placeholder': 'Estado'
        })
    )

    class Meta:
        model = Curso
        fields = ['titulo', 'descripcion', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-input-modern',
                'placeholder': 'Título del Curso'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-textarea-modern',
                'placeholder': 'Descripción detallada',
                'rows': 4
            }),
            # El widget de 'estado' ya no va aquí, lo define el campo explícito
        }

class BloqueContenidoForm(forms.ModelForm):
    """Formulario para bloques de contenido."""

    urls_archivos = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input-modern',
            'placeholder': 'Pega aquí el iframe completo o URLs de archivos (una por línea)',
            'rows': 3,
            'style': 'min-height: 80px;',
            'id': 'id_urls_archivos'
        }),
        help_text='Una URL por línea. Solo para tipo "Archivos".'
    )

    class Meta:
        model = BloqueContenido
        fields = ['seccion', 'tipo', 'titulo', 'descripcion', 'url_recurso', 'render_type']  # ← QUITAR 'orden'
        widgets = {
            'seccion': forms.Select(attrs={'class': 'form-select-modern', 'id': 'id_seccion'}),
            'tipo': forms.Select(attrs={'class': 'form-select-modern', 'id': 'id_tipo_contenido'}),
            'titulo': forms.TextInput(attrs={'class': 'form-input-modern', 'placeholder': 'Título del bloque'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-textarea-modern',
                'placeholder': 'Escribe tu contenido aquí...\n\nPuedes usar:\n- Listas\n**Negrita**\n*Itálica*',
                'rows': 6,
            }),
            'url_recurso': forms.TextInput(attrs={
                'class': 'form-input-modern',
                'placeholder': 'URL del enlace (solo para tipo Enlace Web)',
                'id': 'id_url_recurso'
            }),
            'render_type': forms.Select(attrs={'class': 'form-select-modern', 'id': 'id_render_type'}),
        }
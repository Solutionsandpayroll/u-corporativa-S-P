from django.urls import path
from .views import *

urlpatterns = [

    
    # Rutas de inicio de sesión
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),


]
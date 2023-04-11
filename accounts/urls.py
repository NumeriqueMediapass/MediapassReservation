from django.urls import path
from .views import process_login, logout_view


urlpatterns = [
    path('connexion/', process_login, name='login'),
    path('deconnexion/', logout_view, name='logout'),
]

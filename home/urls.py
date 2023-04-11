from django.urls import path
from .views import index, handler404, search, legal_information

urlpatterns = [
    path('', index, name='home'),
    path('', handler404, name='handler404'),
    path('recherche/', search, name='search'),
    path('mentions-legales/', legal_information, name='legalinformation'),
]

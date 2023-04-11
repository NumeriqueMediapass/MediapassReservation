from django.urls import path
from . import views

urlpatterns = [
    # Gestion des produits
    path('products/', views.product_list, name='product_list'),
    path('produits/', views.product_list_user, name='product_list_user'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/update/<int:pk>/', views.product_update, name='product_update'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    # Gestion des catégories
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/update/<int:pk>/', views.category_update, name='category_update'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    # Gestion des réservations
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('reservations/<int:pk>/', views.reservation_details, name='reservation_details'),
    path('reservation/<int:pk>/approve/', views.approve_reservation, name='approve_reservation'),
    path('reservation/disapprove/<int:pk>/', views.disapprove_reservation, name='disapprove_reservation'),
    path('reservation/<int:pk>/delete/', views.delete_reservation, name='delete_reservation'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    # Gestion des structures
    path('structures/', views.structure_list, name='structure_list'),
    path('structure/inscription', views.structure_create_register, name='structure_create_register'),
    path('structures/<int:pk>/', views.structure_detail, name='structure_detail'),
    path('structures/create/', views.structure_create, name='structure_create'),
    path('structures/update/<int:pk>/', views.structure_update, name='structure_update'),
    path('structures/delete/<int:pk>/', views.structure_delete, name='structure_delete'),
    path('<int:pk>/validate/', views.structure_validate, name='structure_validate'),

]

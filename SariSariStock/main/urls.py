from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('logout/', views.LogOut, name='logout'),
    path('products/', views.products, name='products'),
    path('inventory/', views.inventory, name='inventory'),
    path('pos/', views.pos, name='pos'),
    path('sales/', views.sales, name='sales'),
]
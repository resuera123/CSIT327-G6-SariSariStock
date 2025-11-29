from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('logout/', views.LogOut, name='logout'),
    path('products/', views.products, name='products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('products/archive/<int:product_id>/', views.archive_product, name='archive_product'),
    path('inventory/', views.inventory, name='inventory'),
    path('inventory/add/<int:product_id>/', views.add_stock, name='add_stock'),
    path('inventory/reduce/<int:product_id>/', views.reduce_stock, name='reduce_stock'),
    path('pos/', views.pos, name='pos'),
    path('pos/checkout/', views.checkout_pos, name='checkout_pos'),
    path('sales/', views.sales, name='sales'),
    path('sales/void/<int:sale_id>/', views.void_sale, name='void-sale'), 
]
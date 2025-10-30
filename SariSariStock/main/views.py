from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import RegisterForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .models import Products
from django.db.models import Q

# Create your views here.
@login_required(login_url='/login/')
def home(request):
    return render(request, 'main/home.html')

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {'form': form})

def LogOut(request):
    logout(request)
    return redirect("/login/")

@login_required(login_url='/login/')
def products(request):
    query = request.GET.get('q')
    selected_category = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'active')

    products = Products.objects.filter(user=request.user)
    categories = Products.CATEGORY_CHOICES
    status = Products.STATUS_CHOICES

    if query:
        products = products.filter(Q(name__icontains=query) | Q(code__icontains=query))

    if selected_category != 'all' and selected_category:
        products = products.filter(categories=selected_category)

    if status_filter:
        products = products.filter(status=status_filter)

    return render(request, 'productCatalog/products.html', {
        'products': products,
        'categories': categories,
        'status': status,
        'status_filter': status_filter,
        'query': query,
        'selected_category': selected_category,
    })

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            form.save()
            return redirect('/products')
    else:
        form = ProductForm()

    return render(request, 'productCatalog/add_product.html', {'form': form})

def edit_product(request, product_id):
    product = get_object_or_404(Products, id=product_id, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('/products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'productCatalog/edit_product.html', {'form': form, 'product': product})

def delete_product(request, product_id):
    product = get_object_or_404(Products, id=product_id, user=request.user)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('/products')

    return render(request, 'productCatalog/delete_product.html', {'product': product})

@login_required(login_url='/login/')
def inventory(request):

    products = Products.objects.filter(user=request.user)
    categories = Products.CATEGORY_CHOICES

    return render(request, 'inventory/inventory.html', {
        'products': products,
        'categories': categories,
    })

def add_stock(request, product_id):
    product = get_object_or_404(Products, id=product_id, user=request.user)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))
        if quantity > 0:
            product.quantity += quantity
            product.save()
    return redirect('/inventory') 

@login_required(login_url='/login/')
def pos(request):
    return render(request, 'pos/pos.html')

@login_required(login_url='/login/')
def sales(request):
    return render(request, 'sales/sales.html')
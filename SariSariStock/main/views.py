from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import RegisterForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .models import Products, MovementLog
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
import json

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
 
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/home')
        return super().dispatch(request, *args, **kwargs)

# Create your views here.
@login_required(login_url='/login/')
def home(request):
    return render(request, 'main/home.html')

def sign_up(request):

    if request.user.is_authenticated:
        return redirect('/home')

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
    movement_logs = MovementLog.objects.filter(product__user=request.user).order_by('-date')

    return render(request, 'inventory/inventory.html', {
        'products': products,
        'categories': categories,
        'movement_logs': movement_logs,
    })

@login_required(login_url='/login/')
def add_stock(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity'))
        note = request.POST.get('note', '')

        product.quantity += qty
        product.save()

        local_time = timezone.localtime(timezone.now())

        MovementLog.objects.create(
            product=product,
            reference=f"AS#{local_time.strftime('%H%M%S')}",
            change=qty,
            note=note
        )

    return redirect('/inventory') 

def reduce_stock(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity'))
        note = request.POST.get('note', '')

        if qty > product.quantity:
            qty = product.quantity  # prevent negative stock

        product.quantity -= qty
        product.save()

        local_time = timezone.localtime(timezone.now())

        MovementLog.objects.create(
            product=product,
            reference=f"RS#{local_time.strftime('%H%M%S')}",
            change=-qty,
            note=note
        )

    return redirect('/inventory')

@login_required(login_url='/login/')
def pos(request):
    # Get only active products with quantity > 0
    products = Products.objects.filter(
        user=request.user, 
        status='active',
        quantity__gt=0
    ).order_by('name')
    
    context = {
        'products': products,
    }
    
    return render(request, 'pos/pos.html', context)

@login_required(login_url='/login/')
def checkout_pos(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart_items = data.get('cart', [])
            cash_received = float(data.get('cash_received', 0))
            
            if not cart_items:
                return JsonResponse({'success': False, 'error': 'Cart is empty'})
            
            # Calculate total
            total = 0
            
            # Validate stock
            for item in cart_items:
                product = Products.objects.get(id=item['id'], user=request.user)
                
                # Check if enough stock
                if product.quantity < item['quantity']:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Insufficient stock for {product.name}'
                    })
                
                total += product.price * item['quantity']
            
            # Check if cash received is sufficient
            if cash_received < total:
                return JsonResponse({'success': False, 'error': 'Insufficient cash received'})
            
            # Generate reference code for movement logs
            local_time = timezone.localtime(timezone.now())
            reference_code = f"PS#{local_time.strftime('%H%M%S')}"
            
            # Update product quantities and create movement logs
            for item in cart_items:
                product = Products.objects.get(id=item['id'], user=request.user)
                quantity = item['quantity']
                
                # Update product quantity
                product.quantity -= quantity
                product.save()
                
                # Create movement log
                MovementLog.objects.create(
                    product=product,
                    reference=reference_code,
                    change=-quantity,
                    note=f"Product Sold"
                )
            
            return JsonResponse({
                'success': True,
                'reference': reference_code,
                'total': total
            })
            
        except Products.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})




@login_required(login_url='/login/')
def sales(request):
    return render(request, 'sales/sales.html')
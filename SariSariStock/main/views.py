from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import RegisterForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from .models import Products, MovementLog
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
import json
from django.utils import timezone
from .models import Sales, salesItems, Products
from datetime import date, timedelta

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
 
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/home')
        return super().dispatch(request, *args, **kwargs)

@login_required(login_url='/login/')
def home(request):
    today = timezone.localdate()

    # --- Today's Total Sales ---
    todays_sales = (
        Sales.objects.filter(
            salesitems__product_id__user=request.user,
            date_added__date=today
        )
        .aggregate(total=Sum('grand_total'))['total'] or 0
    )

    # --- Gross Profit (Today) ---
    gross_profit = (
        salesItems.objects.filter(
            product_id__user=request.user,
            sales_id__date_added__date=today
        )
        .annotate(
            profit_per_item=(F('price') - F('product_id__cost')) * F('qty')
        )
        .aggregate(total_profit=Sum('profit_per_item'))['total_profit'] or 0
    )

    # --- Low Stock Items (1–9 units) ---
    low_stock_products = Products.objects.filter(
        user=request.user,
        quantity__lt=10,
        quantity__gt=0,
        status='active'
    )

    # Count of low stock items
    low_stock_count = low_stock_products.count()

    # --- Inventory Value ---
    inventory_value = Products.objects.filter(user=request.user, status='active').aggregate(
        total=Sum(F('cost') * F('quantity'))
    )['total'] or 0

    # --- Top Seller (Today) ---
    top_seller = salesItems.objects.filter(
        product_id__user=request.user,
        sales_id__date_added__date=today
    ).values('product_id__name').annotate(
        total_sold=Sum('qty')
    ).order_by('-total_sold').first()
    top_seller_name = top_seller['product_id__name'] if top_seller else "No sales today"

    # --- Out of Stock (quantity == 0) ---
    out_of_stock_count = Products.objects.filter(user=request.user, quantity=0).count()

    # --- Sales Revenue for last 7 days ---
    sales_labels_7days, sales_values_7days = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        total_sales = Sales.objects.filter(salesitems__product_id__user=request.user, date_added__date=day).aggregate(total=Sum('grand_total'))['total'] or 0
        sales_labels_7days.append(day.strftime("%b %d"))
        sales_values_7days.append(total_sales)
    
    # Last 1 month (30 days)
    sales_labels_1month, sales_values_1month = [], []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        total_sales = Sales.objects.filter(salesitems__product_id__user=request.user, date_added__date=day).aggregate(total=Sum('grand_total'))['total'] or 0
        sales_labels_1month.append(day.strftime("%b %d"))
        sales_values_1month.append(total_sales)

    # Last 1 year (monthly)
    sales_labels_1year, sales_values_1year = [], []
    for i in range(11, -1, -1):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        total_sales = Sales.objects.filter(salesitems__product_id__user=request.user, date_added__year=year, date_added__month=month).aggregate(total=Sum('grand_total'))['total'] or 0
        sales_labels_1year.append(f"{year}-{month:02d}")
        sales_values_1year.append(total_sales)

    context = {
        'todays_sales': todays_sales,
        'gross_profit': gross_profit,
        'low_stock_count': low_stock_count,
        'low_stock_products': low_stock_products,
        'inventory_value': inventory_value,
        'top_seller_name': top_seller_name,
        'out_of_stock_count': out_of_stock_count,
        'sales_labels_7days': sales_labels_7days,
        'sales_values_7days': sales_values_7days,
        'sales_labels_1month': sales_labels_1month,
        'sales_values_1month': sales_values_1month,
        'sales_labels_1year': sales_labels_1year,
        'sales_values_1year': sales_values_1year,  
    }
    return render(request, 'main/home.html', context)

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
    # Auto-archive any active products that have quantity <= 0
    Products.objects.filter(user=request.user, quantity__lte=0, status='active').update(status='archive')

    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'active')

    qs = Products.objects.filter(user=request.user)

    if status_filter in ['active', 'archive']:
        qs = qs.filter(status=status_filter)

    if selected_category and selected_category != 'all':
        qs = qs.filter(categories=selected_category)

    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(code__icontains=query))

    context = {
        'products': qs.order_by('-date_added'),
        'categories': Products.CATEGORY_CHOICES,
        'selected_category': selected_category,
        'status_filter': status_filter,
        'query': query,
    }
    return render(request, 'productCatalog/products.html', context)

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

def archive_product(request, product_id):
    product = get_object_or_404(Products, id=product_id, user=request.user)
    
    # Update status to archive
    product.status = "archive"
    product.save()
    
    return redirect('/products')

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
    product = get_object_or_404(Products, id=product_id, user=request.user)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 0))
        note = request.POST.get('note', '')

        quantity_before = product.quantity
        product.quantity += qty
        # If stock goes above zero, ensure status is active
        if product.quantity > 0 and product.status != 'active':
            product.status = 'active'
        product.save()

        local_time = timezone.localtime(timezone.now())

        MovementLog.objects.create(
            product=product,
            reference=f"AS#{local_time.strftime('%Y%m%d%H%M%S')}",
            quantity_before=quantity_before,
            change=qty,
            quantity_after=product.quantity,
            note=note
        )

    return redirect('/inventory')

def reduce_stock(request, product_id):
    product = get_object_or_404(Products, id=product_id, user=request.user)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 0))
        note = request.POST.get('note', '')

        quantity_before = product.quantity

        # Prevent negative stock
        actual_removed = min(qty, product.quantity)
        product.quantity -= actual_removed

        # If quantity reaches 0, archive the product
        if product.quantity <= 0:
            product.quantity = 0
            product.status = 'archive'

        product.save()

        local_time = timezone.localtime(timezone.now())

        MovementLog.objects.create(
            product=product,
            reference=f"RS#{local_time.strftime('%Y%m%d%H%M%S')}",
            quantity_before=quantity_before,
            change=-actual_removed,
            quantity_after=product.quantity,
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

            total = 0
            # Validate stock
            for item in cart_items:
                product = Products.objects.get(id=item['id'], user=request.user)
                if product.quantity < item['quantity']:
                    return JsonResponse({'success': False, 'error': f'Insufficient stock for {product.name}'})
                total += product.price * item['quantity']

            if cash_received < total:
                return JsonResponse({'success': False, 'error': 'Insufficient cash received'})

            local_time = timezone.localtime(timezone.now())
            sale = Sales.objects.create(
                code=f"SALE#{local_time.strftime('%Y%m%d%H%M%S')}",
                sub_total=total,
                grand_total=total,
                amount_change=cash_received - total
            )

            for item in cart_items:
                product = Products.objects.get(id=item['id'], user=request.user)
                quantity = int(item['quantity'])
                quantity_before = product.quantity

                product.quantity -= quantity
                if product.quantity <= 0:
                    product.quantity = 0
                    product.status = 'archive'
                product.save()

                MovementLog.objects.create(
                    product=product,
                    reference=f"PS#{local_time.strftime('%Y%m%d%H%M%S')}",
                    quantity_before=quantity_before,
                    change=-quantity,
                    quantity_after=product.quantity,
                    note="Product Sold"
                )

                salesItems.objects.create(
                    sales_id=sale,
                    product_id=product,
                    price=product.price,
                    qty=quantity,
                    total=product.price * quantity
                )

            return JsonResponse({'success': True, 'reference': sale.code, 'total': total})

        except Products.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})




@login_required(login_url='/login/')
def sales(request):
    return render(request, 'sales/sales.html')
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Category, Product, Cart, CartItem, Variation, Order, OrderItem
import uuid


def get_or_create_cart(request):
    """Get the current cart or create a new one"""
    if request.user.is_authenticated:
        # Try to get an existing cart for the logged-in user
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session to maintain cart
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(cart_id=cart_id)
            except Cart.DoesNotExist:
                cart = Cart.objects.create()
                request.session['cart_id'] = str(cart.cart_id)
        else:
            cart = Cart.objects.create()
            request.session['cart_id'] = str(cart.cart_id)
    
    return cart


def home(request):
    """View for the home page"""
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'ecommerce/home.html', context)


def product_list(request, category_slug=None):
    """View for product listing, can be filtered by category"""
    category = None
    products = Product.objects.filter(is_active=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    
    # Handle search queries
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Handle sorting
    sort_by = request.GET.get('sort_by', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    context = {
        'category': category,
        'products': products,
        'query': query,
        'sort_by': sort_by,
    }
    return render(request, 'ecommerce/product_list.html', context)


def product_detail(request, slug):
    """View for product details"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variations = product.variations.filter(is_active=True)
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'variations': variations,
        'related_products': related_products,
    }
    return render(request, 'ecommerce/product_detail.html', context)


@require_POST
def add_to_cart(request):
    """Add a product to the cart"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Get selected variations
    variation_ids = []
    for key, value in request.POST.items():
        if key.startswith('variation_'):
            variation_ids.append(int(value))
    
    variations = Variation.objects.filter(id__in=variation_ids, is_active=True)
    
    # Get or create cart
    cart = get_or_create_cart(request)
    
    # Check if this product with same variations is already in cart
    existing_item = None
    for item in cart.items.all():
        if item.product.id == product.id:
            existing_variations = set(item.variations.all().values_list('id', flat=True))
            if set(variation_ids) == existing_variations:
                existing_item = item
                break
    
    # Add to cart or update quantity
    if existing_item:
        existing_item.quantity += quantity
        existing_item.save()
    else:
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        if variations:
            cart_item.variations.add(*variations)
    
    messages.success(request, f"{product.name} added to your cart.")
    return redirect('ecommerce:cart')


def cart(request):
    """View for the shopping cart"""
    cart = get_or_create_cart(request)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'ecommerce/cart.html', context)


@require_POST
def update_cart(request):
    """Update cart item quantity"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity'))
    
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify this cart item belongs to the current user's cart
    cart = get_or_create_cart(request)
    if cart_item.cart.id != cart.id:
        messages.error(request, "You don't have permission to modify this cart.")
        return redirect('ecommerce:cart')
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('ecommerce:cart')


def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify this cart item belongs to the current user's cart
    cart = get_or_create_cart(request)
    if cart_item.cart.id != cart.id:
        messages.error(request, "You don't have permission to modify this cart.")
        return redirect('ecommerce:cart')
    
    cart_item.delete()
    messages.success(request, f"{cart_item.product.name} removed from your cart.")
    return redirect('ecommerce:cart')


@login_required
def checkout(request):
    """Checkout page"""
    cart = get_or_create_cart(request)
    
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('ecommerce:product_list')
    
    if request.method == 'POST':
        # Process the order
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            country=request.POST.get('country'),
            zipcode=request.POST.get('zipcode'),
            payment_method=request.POST.get('payment_method'),
            total_price=cart.total_price,
            ip=request.META.get('REMOTE_ADDR'),
            order_note=request.POST.get('order_note', ''),
        )
        
        # Create order items
        for cart_item in cart.items.all():
            order_item = OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
            # Add variations
            if cart_item.variations.exists():
                order_item.variation.add(*cart_item.variations.all())
        
        # Clear the cart
        cart.items.all().delete()
        
        messages.success(request, f"Order {order.order_number} placed successfully!")
        return redirect('ecommerce:order_complete', order_id=order.id)
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
    }
    return render(request, 'ecommerce/checkout.html', context)


@login_required
def order_complete(request, order_id):
    """Order completed page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'ecommerce/order_complete.html', context)


@login_required
def my_orders(request):
    """View for user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    return render(request, 'ecommerce/my_orders.html', context)

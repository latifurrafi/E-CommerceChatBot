import os
import django
from django.utils import timezone
from django.utils.text import slugify
import uuid
import random
from faker import Faker

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbchatbot.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from ecommerce.models import Category, Product, ProductImage, Variation, Cart, CartItem, Order, OrderItem  # Fixed import path

fake = Faker()

def create_users():
    users = []
    for i in range(10):
        try:
            user = User.objects.create_user(username=f'user{i}', email=fake.email(), password='password123')
            users.append(user)
        except:
            try:
                user = User.objects.get(username=f'user{i}')
                users.append(user)
            except User.DoesNotExist:
                pass
    return users

def create_categories():
    categories_data = ['Electronics', 'Clothing', 'Books', 'Home Goods', 'Sports']
    categories = []
    for cat_name in categories_data:
        category, created = Category.objects.get_or_create(name=cat_name)
        category.description = fake.sentence()
        category.save()
        categories.append(category)
    return categories

def create_products(categories):
    products = []
    for i in range(20):
        category = random.choice(categories)
        name = f"Product {fake.unique.word().capitalize()}_{i}"
        price = round(random.uniform(10, 500), 2)
        sale_price = round(price * random.uniform(0.7, 0.9), 2) if random.random() < 0.4 else None

        product, created = Product.objects.get_or_create(
            category=category,
            name=name,
            defaults={
                'description': fake.paragraph(nb_sentences=5),
                'price': price,
                'sale_price': sale_price,
                'sku': fake.unique.ean13(),
                'stock': random.randint(0, 200),
                'is_active': random.choice([True, False]),
                'is_featured': random.choice([True, False]),
            }
        )

        products.append(product)

        # Create product images
        num_images = random.randint(1, 3)
        for j in range(num_images):
            ProductImage.objects.create(
                product=product,
                image='products/dummy.jpg',
                alt_text=fake.sentence(nb_words=4),
                is_primary=(j == 0),
            )

        # Create variations
        variation_types = random.sample(Variation.VARIATION_TYPE_CHOICES, random.randint(1, 2))
        for var_type, _ in variation_types:
            Variation.objects.create(
                product=product,
                variation_type=var_type,
                name=fake.word().capitalize(),
                price_adjustment=round(random.uniform(-10, 20), 2),
                stock=random.randint(0, 50),
                is_active=True,
            )

    return products

def create_carts(users, products):
    carts = []
    for i in range(15):
        user = random.choice([None] + users)
        cart = Cart.objects.create(user=user)
        carts.append(cart)

        # Add cart items
        for _ in range(random.randint(1, 5)):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)

            # Add variations
            available_variations = Variation.objects.filter(product=product)
            if available_variations.exists():
                num_variations = min(random.randint(0, 2), len(available_variations))
                if num_variations > 0:
                    cart_item.variations.set(random.sample(list(available_variations), num_variations))

    return carts

def create_orders(users, products):
    orders = []
    for i in range(25):
        user = random.choice(users)
        first_name = fake.first_name()
        last_name = fake.last_name()
        total_price = round(random.uniform(50, 1000), 2)

        order = Order.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.address(),
            city=fake.city(),
            state=fake.state_abbr(),
            country=fake.country(),
            zipcode=fake.zipcode(),
            total_price=total_price,
            payment_method=random.choice(['Credit Card', 'PayPal', 'Cash on Delivery']),
            status=random.choice(['pending', 'processing', 'shipped', 'delivered', 'cancelled']),
            ip=fake.ipv4(),
            order_note=fake.sentence() if random.random() < 0.3 else None,
        )

        orders.append(order)

        # Create order items
        for _ in range(random.randint(1, 4)):
            product = random.choice(products)
            quantity = random.randint(1, 2)
            price = product.sale_price if product.sale_price else product.price

            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price,
            )

            # Add variations
            available_variations = Variation.objects.filter(product=product)
            if available_variations.exists():
                num_variations = min(random.randint(0, 2), len(available_variations))
                if num_variations > 0:
                    order_item.variation.set(random.sample(list(available_variations), num_variations))

    return orders

def run_data_generation():
    print("Starting data generation...")
    users = create_users()
    categories = create_categories()
    products = create_products(categories)
    create_carts(users, products)
    create_orders(users, products)
    print("Data generation completed successfully.")

if __name__ == '__main__':
    run_data_generation()

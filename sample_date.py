import os
import django
import random
from decimal import Decimal

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dbchatbot.settings")
django.setup()

from chatapp.models import Product, FAQ, Order, OrderItem

def create_sample_products():
    """Create sample products"""
    products = [
        {
            'name': 'Smartphone X',
            'description': 'Latest smartphone with 6.5 inch display, 128GB storage, and dual camera.',
            'price': '699.99',
            'sku': 'PHN-X-128'
        },
        {
            'name': 'Laptop Pro',
            'description': 'Powerful laptop with 16GB RAM, 512GB SSD, and dedicated graphics card.',
            'price': '1299.99',
            'sku': 'LPT-PRO-512'
        },
        {
            'name': 'Wireless Earbuds',
            'description': 'Premium wireless earbuds with noise cancellation and 8 hours battery life.',
            'price': '129.99',
            'sku': 'AUD-WL-NC'
        },
        {
            'name': 'Smart Watch',
            'description': 'Fitness tracker with heart rate monitor, GPS and 5-day battery life.',
            'price': '199.99',
            'sku': 'WCH-SMT-5D'
        },
        {
            'name': 'Digital Camera',
            'description': '24MP digital camera with 4K video recording and 30x optical zoom.',
            'price': '549.99',
            'sku': 'CAM-DIG-24MP'
        }
    ]
    
    for product_data in products:
        Product.objects.create(
            name=product_data['name'],
            description=product_data['description'],
            price=Decimal(product_data['price']),
            sku=product_data['sku']
        )
    
    print(f"Created {len(products)} products")

def create_sample_faqs():
    """Create sample FAQs"""
    faqs = [
        {
            'question': 'How long does shipping take?',
            'answer': 'Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days.',
            'category': 'Shipping'
        },
        {
            'question': 'What is your return policy?',
            'answer': 'You can return items within 30 days of delivery for a full refund.',
            'category': 'Returns'
        },
        {
            'question': 'Do you ship internationally?',
            'answer': 'Yes, we ship to most countries worldwide. International shipping typically takes 7-14 business days.',
            'category': 'Shipping'
        },
        {
            'question': 'How can I track my order?',
            'answer': 'You can track your order by logging into your account or using the tracking number provided in your shipping confirmation email.',
            'category': 'Orders'
        },
        {
            'question': 'Are your products covered by warranty?',
            'answer': 'Yes, all our electronic products come with a 1-year manufacturer warranty.',
            'category': 'Warranty'
        }
    ]
    
    for faq_data in faqs:
        FAQ.objects.create(
            question=faq_data['question'],
            answer=faq_data['answer'],
            category=faq_data['category']
        )
    
    print(f"Created {len(faqs)} FAQs")

def create_sample_orders():
    """Create sample orders"""
    # Get all products
    products = list(Product.objects.all())
    
    # Customer data
    customers = [
        {'name': 'John Smith', 'email': 'john.smith@example.com'},
        {'name': 'Sarah Johnson', 'email': 'sarah.j@example.com'},
        {'name': 'Michael Brown', 'email': 'mbrown@example.com'},
        {'name': 'Emily Wilson', 'email': 'emily.wilson@example.com'},
        {'name': 'David Lee', 'email': 'david.lee@example.com'}
    ]
    
    # Order statuses
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    # Create orders
    for i in range(1, 11):  # Create 10 orders
        # Select a random customer
        customer = random.choice(customers)
        
        # Create order
        order = Order.objects.create(
            order_number=f'ORD-2023-{i:04d}',
            customer_name=customer['name'],
            customer_email=customer['email'],
            status=random.choice(statuses),
            total_amount=Decimal('0.00')  # Will be updated
        )
        
        # Add 1-3 random products to the order
        num_items = random.randint(1, 3)
        total_amount = Decimal('0.00')
        
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            item_price = product.price
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=item_price
            )
            
            total_amount += item_price * quantity
        
        # Update order total
        order.total_amount = total_amount
        order.save()
    
    print(f"Created 10 orders")

def main():
    """Create all sample data"""
    # Check if data already exists
    if Product.objects.exists() or FAQ.objects.exists() or Order.objects.exists():
        print("Data already exists. Skipping sample data creation.")
        return
    
    create_sample_products()
    create_sample_faqs()
    create_sample_orders()
    
    print("Sample data creation complete!")

if __name__ == "__main__":
    main()

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import logging
from .embedding_manager import EntityEmbeddingManager
from .models import Product, FAQ, Order, OrderItem  # Import all models that need embeddings

logger = logging.getLogger(__name__)

# Initialize the embedding manager
embedding_manager = EntityEmbeddingManager(
    embedding_dir=getattr(settings, 'EMBEDDING_DIR', 'embeddings')
)

# Product signals
@receiver(post_save, sender=Product)
def update_product_embeddings(sender, instance, created, **kwargs):
    """Update product embeddings when a product is created or updated"""
    try:
        # Convert product instance to dictionary
        product_data = {
            'id': str(instance.id),
            'name': instance.name,
            'description': instance.description,
            'price': float(instance.price),
            'categories': [cat.name for cat in instance.categories.all()] if hasattr(instance, 'categories') else [],
            'brand': instance.brand.name if hasattr(instance, 'brand') and instance.brand else None,
            'specifications': instance.specifications if hasattr(instance, 'specifications') else {},
            'sku': instance.sku
        }
        
        # Update embeddings
        success = embedding_manager.update_product(product_data)
        if success:
            logger.info(f"{'Created' if created else 'Updated'} embeddings for product {instance.id}")
        else:
            logger.error(f"Failed to {'create' if created else 'update'} embeddings for product {instance.id}")
            
    except Exception as e:
        logger.error(f"Error updating product embeddings: {e}")

@receiver(post_delete, sender=Product)
def delete_product_embeddings(sender, instance, **kwargs):
    """Delete product embeddings when a product is deleted"""
    try:
        success = embedding_manager.delete_product(str(instance.id))
        if success:
            logger.info(f"Deleted embeddings for product {instance.id}")
        else:
            logger.error(f"Failed to delete embeddings for product {instance.id}")
            
    except Exception as e:
        logger.error(f"Error deleting product embeddings: {e}")

# FAQ signals
@receiver(post_save, sender=FAQ)
def update_faq_embeddings(sender, instance, created, **kwargs):
    """Update FAQ embeddings when a FAQ is created or updated"""
    try:
        # Convert FAQ instance to dictionary
        faq_data = {
            'id': str(instance.id),
            'question': instance.question,
            'answer': instance.answer,
            'category': instance.category if hasattr(instance, 'category') else ''
        }
        
        # Update embeddings
        success = embedding_manager.update_faq(faq_data)
        if success:
            logger.info(f"{'Created' if created else 'Updated'} embeddings for FAQ {instance.id}")
        else:
            logger.error(f"Failed to {'create' if created else 'update'} embeddings for FAQ {instance.id}")
            
    except Exception as e:
        logger.error(f"Error updating FAQ embeddings: {e}")

@receiver(post_delete, sender=FAQ)
def delete_faq_embeddings(sender, instance, **kwargs):
    """Delete FAQ embeddings when a FAQ is deleted"""
    try:
        success = embedding_manager.delete_faq(str(instance.id))
        if success:
            logger.info(f"Deleted embeddings for FAQ {instance.id}")
        else:
            logger.error(f"Failed to delete embeddings for FAQ {instance.id}")
            
    except Exception as e:
        logger.error(f"Error deleting FAQ embeddings: {e}")

# Order signals
@receiver(post_save, sender=Order)
def update_order_embeddings(sender, instance, created, **kwargs):
    """Update order embeddings when an order is created or updated"""
    try:
        # Get order items
        order_items = OrderItem.objects.filter(order=instance)
        items_data = []
        for item in order_items:
            items_data.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price)
            })
        
        # Convert order instance to dictionary
        order_data = {
            'id': str(instance.id),
            'order_number': instance.order_number,
            'customer_name': instance.customer_name,
            'customer_email': instance.customer_email,
            'status': instance.status,
            'total_amount': float(instance.total_amount),
            'items': items_data
        }
        
        # Update embeddings
        success = embedding_manager.update_order(order_data)
        if success:
            logger.info(f"{'Created' if created else 'Updated'} embeddings for order {instance.id}")
        else:
            logger.error(f"Failed to {'create' if created else 'update'} embeddings for order {instance.id}")
            
    except Exception as e:
        logger.error(f"Error updating order embeddings: {e}")

@receiver(post_delete, sender=Order)
def delete_order_embeddings(sender, instance, **kwargs):
    """Delete order embeddings when an order is deleted"""
    try:
        success = embedding_manager.delete_order(str(instance.id))
        if success:
            logger.info(f"Deleted embeddings for order {instance.id}")
        else:
            logger.error(f"Failed to delete embeddings for order {instance.id}")
            
    except Exception as e:
        logger.error(f"Error deleting order embeddings: {e}") 
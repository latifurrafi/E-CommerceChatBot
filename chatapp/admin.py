from django.contrib import admin
from .models import Product, FAQ, Order, OrderItem, Embedding
from unfold.admin import ModelAdmin


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'price', 'sku', 'created_at', 'updated_at')
    search_fields = ('name', 'sku')
    list_filter = ('created_at', 'updated_at')


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ('question', 'category', 'created_at', 'updated_at')
    search_fields = ('question', 'category')
    list_filter = ('category',)


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_number', 'customer_name', 'status', 'total_amount', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    list_filter = ('status', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__order_number', 'product__name')


@admin.register(Embedding)
class EmbeddingAdmin(ModelAdmin):
    list_display = ('content_type', 'content_id', 'embedding_file')
    search_fields = ('content_type', 'text_content')

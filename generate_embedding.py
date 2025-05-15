import os
import numpy as np 
import faiss
import json
import django
import logging
from tqdm import tqdm
from sentence_transformers import SentenceTransformer  

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dbchatbot.settings")
django.setup()

from chatapp.models import Product, FAQ, Order, OrderItem, Embedding

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseEmbedder:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2', token='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'):
        logger.info(f"Loading Model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dir = 'embeddings'
        os.makedirs(self.embedding_dir, exist_ok=True)
        print('loaded--------------------------------')

        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.content_mapping = []

    def _get_product_text(self, product):
        return f"Product: {product.name}. Description: {product.description}. Price: ${product.price}. SKU: {product.sku}."

    def _get_faq_text(self, faq):
        return f"Questions: {faq.question} Answer: {faq.answer}"

    def _get_order_text(self, order):
        items = OrderItem.objects.filter(order=order)
        items_text = "; ".join([f"{item.quantity} X {item.product.name}" for item in items])
        return f"Order #{order.order_number} by {order.customer_name}. Status: {order.status}. Total: ${order.total_amount}. Items: {items_text}"

    def embed_products(self):
        logger.info("Embedding Products..............................")
        products = Product.objects.all()
        for product in tqdm(products):
            text = self._get_product_text(product)
            embedding = self.model.encode([text])[0]

            self.index.add(np.array([embedding], dtype=np.float32))
            self.content_mapping.append({
                'type': 'product',
                'id': product.id,
                'text': text
            })


            Embedding.objects.update_or_create(
                content_type='product',
                content_id=product.id,
                defaults={
                    'text_content': text,
                    'embedding_file': f"{self.embedding_dir}/product_{product.id}.npy"
                }
            )

            np.save(f"{self.embedding_dir}/product_{product.id}.npy", embedding)

    def embed_faq(self):
        logger.info("Embedding FAQs.......................")

        faqs = FAQ.objects.all()
        for faq in tqdm(faqs):
            text = self._get_faq_text(faq)
            embedding = self.model.encode([text])[0]
            
            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))
            self.content_mapping.append({
                'type': 'faq',
                'id': faq.id,
                'text': text
            })
            
            # Save to database
            Embedding.objects.update_or_create(
                content_type='faq',
                content_id=faq.id,
                defaults={
                    'text_content': text,
                    'embedding_file': f"{self.embedding_dir}/faq_{faq.id}.npy"
                }
            )
            
            # Save as file for backup
            np.save(f"{self.embedding_dir}/faq_{faq.id}.npy", embedding)
    
    def embed_orders(self):
        """Embed all orders"""
        logger.info("Embedding orders..........................................")
        orders = Order.objects.all()
        for order in tqdm(orders):
            text = self._get_order_text(order)
            embedding = self.model.encode([text])[0]
            
            # Add to FAISS index
            self.index.add(np.array([embedding], dtype=np.float32))
            self.content_mapping.append({
                'type': 'order',
                'id': order.id,
                'text': text
            })
            
            # Save to database
            Embedding.objects.update_or_create(
                content_type='order',
                content_id=order.id,
                defaults={
                    'text_content': text,
                    'embedding_file': f"{self.embedding_dir}/order_{order.id}.npy"
                }
            )
            
            # Save as file for backup
            np.save(f"{self.embedding_dir}/order_{order.id}.npy", embedding)
    

    def save_index(self):
        logger.info("Saving FAISS index....")
        faiss.write_index(self.index, f"{self.embedding_dir}/faiss_index.bin")

        with open(f'{self.embedding_dir}/content_mapping.json', 'w') as f:
            json.dump(self.content_mapping, f)

    def embed_all(self):
        self.embed_products()
        self.embed_faq()
        self.embed_orders()
        self.save_index()
        logger.info(f"Embedded {len(self.content_mapping)} items")

if __name__ == "__main__":
    embedder = DatabaseEmbedder()
    embedder.embed_all()
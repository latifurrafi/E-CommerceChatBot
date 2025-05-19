import os
import numpy as np
import faiss
import json
import logging
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EntityEmbeddingManager:
    """Manages embeddings for different entity types in a vector database"""
    
    def __init__(self, embedding_dir='embeddings', model_name='sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize the embedding manager with the given model and directory."""
        self.embedding_dir = embedding_dir
        os.makedirs(self.embedding_dir, exist_ok=True)
        
        try:
            # Load the model
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            
            # Initialize or load the FAISS index
            self.index_path = f"{self.embedding_dir}/faiss_index.bin"
            self.mapping_path = f"{self.embedding_dir}/content_mapping.json"
            
            if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, 'r') as f:
                    self.content_mapping = json.load(f)
                logger.info(f"Loaded existing index with {len(self.content_mapping)} items")
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                self.content_mapping = []
                logger.info("Created new FAISS index")
                
        except Exception as e:
            logger.error(f"Error initializing EntityEmbeddingManager: {e}")
            raise
    
    def _get_entity_text(self, entity_type: str, entity_data: Dict[str, Any]) -> str:
        """Convert entity data to a text representation for embedding based on entity type."""
        if entity_type == 'product':
            return self._get_product_text(entity_data)
        elif entity_type == 'faq':
            return self._get_faq_text(entity_data)
        elif entity_type == 'order':
            return self._get_order_text(entity_data)
        else:
            # Generic fallback for unknown entity types
            return " ".join([f"{k}: {v}" for k, v in entity_data.items() if k != 'id'])
    
    def _get_product_text(self, product: Dict[str, Any]) -> str:
        """Convert product data to a text representation for embedding."""
        text = f"Product: {product['name']}. "
        text += f"Description: {product['description']}. "
        text += f"Price: ${product['price']}. "
        
        if 'categories' in product and product['categories']:
            text += f"Categories: {', '.join(product['categories'])}. "
        
        if 'brand' in product and product['brand']:
            text += f"Brand: {product['brand']}. "
            
        if 'specifications' in product and product['specifications']:
            specs = product['specifications']
            if isinstance(specs, dict):
                specs_text = '; '.join(f"{k}: {v}" for k, v in specs.items())
                text += f"Specifications: {specs_text}."
        
        return text
    
    def _get_faq_text(self, faq: Dict[str, Any]) -> str:
        """Convert FAQ data to a text representation for embedding."""
        text = f"Question: {faq['question']}. "
        text += f"Answer: {faq['answer']}. "
        
        if 'category' in faq and faq['category']:
            text += f"Category: {faq['category']}."
            
        return text
    
    def _get_order_text(self, order: Dict[str, Any]) -> str:
        """Convert order data to a text representation for embedding."""
        text = f"Order #{order['order_number']} by {order['customer_name']}. "
        text += f"Status: {order['status']}. "
        text += f"Total: ${order['total_amount']}. "
        
        if 'items' in order and order['items']:
            items_text = "; ".join([f"{item.get('quantity', 1)} X {item.get('product_name', 'Unknown')}" 
                                   for item in order['items']])
            text += f"Items: {items_text}."
            
        return text
    
    def update_entity(self, entity_type: str, entity_data: Dict[str, Any]) -> bool:
        """Update or create embeddings for an entity."""
        try:
            entity_id = str(entity_data['id'])
            entity_text = self._get_entity_text(entity_type, entity_data)
            
            # Generate embedding
            embedding = self.model.encode([entity_text])[0]
            
            # Check if this entity already exists in the mapping
            existing_idx = None
            for idx, item in enumerate(self.content_mapping):
                if item['type'] == entity_type and str(item['id']) == entity_id:
                    existing_idx = idx
                    break
            
            # If exists, update the index
            if existing_idx is not None:
                # Remove old embedding from FAISS (by rebuilding the index)
                old_vectors = []
                for i, item in enumerate(self.content_mapping):
                    if i != existing_idx:
                        item_path = f"{self.embedding_dir}/{item['type']}_{item['id']}.npy"
                        if os.path.exists(item_path):
                            old_vectors.append(np.load(item_path))
                
                # Rebuild index
                self.index = faiss.IndexFlatL2(self.dimension)
                if old_vectors:
                    self.index.add(np.array(old_vectors, dtype=np.float32))
                
                # Update mapping
                self.content_mapping[existing_idx]['text'] = entity_text
            else:
                # Add new embedding to FAISS
                self.index.add(np.array([embedding], dtype=np.float32))
                
                # Add to mapping
                self.content_mapping.append({
                    'type': entity_type,
                    'id': entity_id,
                    'text': entity_text
                })
            
            # Save embedding file
            np.save(f"{self.embedding_dir}/{entity_type}_{entity_id}.npy", embedding)
            
            # Save updated index and mapping
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, 'w') as f:
                json.dump(self.content_mapping, f)
            
            logger.info(f"Successfully updated embeddings for {entity_type} {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating {entity_type} embeddings: {e}")
            return False
    
    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """Delete embeddings for an entity."""
        try:
            entity_id = str(entity_id)
            
            # Find the entity in the mapping
            existing_idx = None
            for idx, item in enumerate(self.content_mapping):
                if item['type'] == entity_type and str(item['id']) == entity_id:
                    existing_idx = idx
                    break
            
            if existing_idx is None:
                logger.warning(f"{entity_type.capitalize()} {entity_id} not found in embeddings")
                return False
            
            # Remove from mapping
            self.content_mapping.pop(existing_idx)
            
            # Rebuild the index without this entity
            self.index = faiss.IndexFlatL2(self.dimension)
            vectors = []
            for item in self.content_mapping:
                item_path = f"{self.embedding_dir}/{item['type']}_{item['id']}.npy"
                if os.path.exists(item_path):
                    vectors.append(np.load(item_path))
            
            if vectors:
                self.index.add(np.array(vectors, dtype=np.float32))
            
            # Delete the embedding file
            embedding_path = f"{self.embedding_dir}/{entity_type}_{entity_id}.npy"
            if os.path.exists(embedding_path):
                os.remove(embedding_path)
            
            # Save updated index and mapping
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, 'w') as f:
                json.dump(self.content_mapping, f)
            
            logger.info(f"Successfully deleted embeddings for {entity_type} {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {entity_type} embeddings: {e}")
            return False
    
    # Convenience methods that call the generic methods
    def update_product(self, product_data: Dict[str, Any]) -> bool:
        return self.update_entity('product', product_data)
    
    def delete_product(self, product_id: str) -> bool:
        return self.delete_entity('product', product_id)
    
    def update_faq(self, faq_data: Dict[str, Any]) -> bool:
        return self.update_entity('faq', faq_data)
    
    def delete_faq(self, faq_id: str) -> bool:
        return self.delete_entity('faq', faq_id)
    
    def update_order(self, order_data: Dict[str, Any]) -> bool:
        return self.update_entity('order', order_data)
    
    def delete_order(self, order_id: str) -> bool:
        return self.delete_entity('order', order_id) 
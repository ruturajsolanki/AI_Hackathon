"""
Knowledge Base Service

Loads and provides access to the knowledge base CSV files for AI agents.
This enables context-aware responses based on customer, product, and policy data.

Uses cosine similarity for semantic matching when embeddings are available,
with fallback to keyword matching for offline operation.
"""

import csv
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _tokenize(text: str) -> List[str]:
    """Simple tokenization: lowercase, split on non-alphanumeric."""
    return re.findall(r'\b[a-z]+\b', text.lower())


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    """Compute term frequency."""
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    # Normalize by total tokens
    total = len(tokens) if tokens else 1
    return {k: v / total for k, v in tf.items()}


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Compute cosine similarity between two TF vectors."""
    if not vec1 or not vec2:
        return 0.0
    
    # Get all unique terms
    all_terms = set(vec1.keys()) | set(vec2.keys())
    
    # Compute dot product and magnitudes
    dot_product = 0.0
    mag1 = 0.0
    mag2 = 0.0
    
    for term in all_terms:
        v1 = vec1.get(term, 0.0)
        v2 = vec2.get(term, 0.0)
        dot_product += v1 * v2
        mag1 += v1 * v1
        mag2 += v2 * v2
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (math.sqrt(mag1) * math.sqrt(mag2))


class KnowledgeBase:
    """
    In-memory knowledge base loaded from CSV files.
    Provides search and lookup methods for AI agents.
    Uses cosine similarity for better semantic matching.
    """
    
    def __init__(self):
        self._knowledge: List[Dict[str, str]] = []
        self._customers: Dict[str, Dict[str, Any]] = {}
        self._products: Dict[str, Dict[str, Any]] = {}
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._faqs: List[Dict[str, Any]] = []
        self._loaded = False
        
        # Pre-computed TF vectors for faster similarity search
        self._knowledge_vectors: List[Tuple[Dict[str, float], Dict[str, str]]] = []
        self._faq_vectors: List[Tuple[Dict[str, float], Dict[str, Any]]] = []
        self._product_vectors: List[Tuple[Dict[str, float], Dict[str, Any]]] = []
    
    def load(self) -> None:
        """Load all CSV data files into memory."""
        if self._loaded:
            return
        
        try:
            self._load_knowledge_base()
            self._load_customers()
            self._load_products()
            self._load_orders()
            self._load_faqs()
            self._build_vectors()
            self._loaded = True
            logger.info("Knowledge base loaded successfully with cosine similarity support")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    def _load_csv(self, filename: str) -> List[Dict[str, str]]:
        """Load a CSV file and return list of dictionaries."""
        filepath = DATA_DIR / filename
        if not filepath.exists():
            logger.warning(f"CSV file not found: {filepath}")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _load_knowledge_base(self) -> None:
        """Load the main knowledge base (problems/solutions)."""
        self._knowledge = self._load_csv("knowledge_base.csv")
        logger.info(f"Loaded {len(self._knowledge)} knowledge base entries")
    
    def _load_customers(self) -> None:
        """Load customer data."""
        customers = self._load_csv("customers.csv")
        self._customers = {c['customer_id']: c for c in customers}
        logger.info(f"Loaded {len(self._customers)} customers")
    
    def _load_products(self) -> None:
        """Load product catalog."""
        products = self._load_csv("products.csv")
        self._products = {p['product_id']: p for p in products}
        logger.info(f"Loaded {len(self._products)} products")
    
    def _load_orders(self) -> None:
        """Load orders data."""
        orders = self._load_csv("orders.csv")
        self._orders = {o['order_id']: o for o in orders}
        logger.info(f"Loaded {len(self._orders)} orders")
    
    def _load_faqs(self) -> None:
        """Load FAQs."""
        self._faqs = self._load_csv("faqs.csv")
        logger.info(f"Loaded {len(self._faqs)} FAQs")
    
    def _build_vectors(self) -> None:
        """Pre-compute TF vectors for all searchable content."""
        # Build knowledge base vectors
        self._knowledge_vectors = []
        for entry in self._knowledge:
            # Combine problem, keywords, category, subcategory for richer matching
            text = " ".join([
                entry.get('problem', ''),
                entry.get('keywords', ''),
                entry.get('category', ''),
                entry.get('subcategory', ''),
                entry.get('solution', '')[:100],  # First 100 chars of solution
            ])
            tokens = _tokenize(text)
            tf = _compute_tf(tokens)
            self._knowledge_vectors.append((tf, entry))
        
        # Build FAQ vectors
        self._faq_vectors = []
        for faq in self._faqs:
            text = " ".join([
                faq.get('question', ''),
                faq.get('keywords', ''),
                faq.get('category', ''),
                faq.get('answer', '')[:100],
            ])
            tokens = _tokenize(text)
            tf = _compute_tf(tokens)
            self._faq_vectors.append((tf, faq))
        
        # Build product vectors
        self._product_vectors = []
        for product in self._products.values():
            text = " ".join([
                product.get('name', ''),
                product.get('category', ''),
                product.get('subcategory', ''),
                product.get('common_issues', ''),
                product.get('description', ''),
            ])
            tokens = _tokenize(text)
            tf = _compute_tf(tokens)
            self._product_vectors.append((tf, product))
        
        logger.info(f"Built {len(self._knowledge_vectors)} KB vectors, {len(self._faq_vectors)} FAQ vectors, {len(self._product_vectors)} product vectors")
    
    # -------------------------------------------------------------------------
    # Search Methods with Cosine Similarity
    # -------------------------------------------------------------------------
    
    def search_solutions(self, query: str, limit: int = 3, min_score: float = 0.05) -> List[Dict[str, str]]:
        """
        Search knowledge base for relevant solutions using cosine similarity.
        Falls back to keyword matching if needed.
        """
        if not self._loaded:
            self.load()
        
        # Compute query vector
        query_tokens = _tokenize(query)
        query_tf = _compute_tf(query_tokens)
        
        # Score all entries by cosine similarity
        scored_results = []
        for vec, entry in self._knowledge_vectors:
            score = _cosine_similarity(query_tf, vec)
            
            # Boost score for exact keyword matches
            keywords = entry.get('keywords', '').lower().split(',')
            query_lower = query.lower()
            for keyword in keywords:
                if keyword.strip() in query_lower:
                    score += 0.1
            
            if score >= min_score:
                scored_results.append((score, entry))
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_results[:limit]]
    
    def search_faqs(self, query: str, limit: int = 3, min_score: float = 0.05) -> List[Dict[str, Any]]:
        """Search FAQs using cosine similarity."""
        if not self._loaded:
            self.load()
        
        query_tokens = _tokenize(query)
        query_tf = _compute_tf(query_tokens)
        
        scored_results = []
        for vec, faq in self._faq_vectors:
            score = _cosine_similarity(query_tf, vec)
            
            # Boost for keyword matches
            keywords = faq.get('keywords', '').lower().split(',')
            query_lower = query.lower()
            for keyword in keywords:
                if keyword.strip() in query_lower:
                    score += 0.1
            
            if score >= min_score:
                scored_results.append((score, faq))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [faq for _, faq in scored_results[:limit]]
    
    def search_products(self, query: str, limit: int = 5, min_score: float = 0.03) -> List[Dict[str, Any]]:
        """Search products using cosine similarity."""
        if not self._loaded:
            self.load()
        
        query_tokens = _tokenize(query)
        query_tf = _compute_tf(query_tokens)
        
        scored_results = []
        for vec, product in self._product_vectors:
            score = _cosine_similarity(query_tf, vec)
            
            # Boost for name match
            name_lower = product.get('name', '').lower()
            if any(token in name_lower for token in query_tokens):
                score += 0.15
            
            if score >= min_score:
                scored_results.append((score, product))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [product for _, product in scored_results[:limit]]
    
    def get_solution_for_category(self, category: str, subcategory: Optional[str] = None) -> List[Dict[str, str]]:
        """Get all solutions for a category."""
        if not self._loaded:
            self.load()
        
        results = []
        for entry in self._knowledge:
            if entry.get('category', '').lower() == category.lower():
                if subcategory is None or entry.get('subcategory', '').lower() == subcategory.lower():
                    results.append(entry)
        
        return results
    
    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        if not self._loaded:
            self.load()
        return self._customers.get(customer_id)
    
    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """Search customers by name or email."""
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        results = []
        
        for customer in self._customers.values():
            name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".lower()
            email = customer.get('email', '').lower()
            
            if query_lower in name or query_lower in email:
                results.append(customer)
        
        return results
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        if not self._loaded:
            self.load()
        return self._products.get(product_id)
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        if not self._loaded:
            self.load()
        return self._orders.get(order_id)
    
    def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a customer."""
        if not self._loaded:
            self.load()
        
        return [
            order for order in self._orders.values()
            if order.get('customer_id') == customer_id
        ]
    
    # -------------------------------------------------------------------------
    # Context Building for LLM
    # -------------------------------------------------------------------------
    
    def build_context_for_query(self, query: str, customer_id: Optional[str] = None) -> str:
        """
        Build a context string for LLM prompts based on the query.
        Uses cosine similarity to find the most relevant information.
        """
        if not self._loaded:
            self.load()
        
        context_parts = []
        
        # Add relevant solutions (with similarity scores)
        solutions = self.search_solutions(query, limit=2)
        if solutions:
            context_parts.append("RELEVANT KNOWLEDGE BASE ENTRIES:")
            for sol in solutions:
                context_parts.append(f"- Problem: {sol.get('problem', 'N/A')}")
                context_parts.append(f"  Solution: {sol.get('solution', 'N/A')}")
                context_parts.append(f"  Department: {sol.get('department', 'N/A')}")
                requires_human = sol.get('requires_human', 'false').lower() == 'true'
                context_parts.append(f"  Requires Human: {'Yes' if requires_human else 'No'}")
                context_parts.append("")
        
        # Add customer context if available
        if customer_id:
            customer = self.get_customer(customer_id)
            if customer:
                context_parts.append("CUSTOMER INFORMATION:")
                context_parts.append(f"- Name: {customer.get('first_name', '')} {customer.get('last_name', '')}")
                context_parts.append(f"- Membership: {customer.get('membership_tier', 'standard')}")
                context_parts.append(f"- Total Orders: {customer.get('total_orders', '0')}")
                context_parts.append(f"- Loyalty Points: {customer.get('loyalty_points', '0')}")
                context_parts.append(f"- Notes: {customer.get('notes', 'None')}")
                context_parts.append("")
                
                # Add recent orders
                orders = self.get_customer_orders(customer_id)
                if orders:
                    context_parts.append("RECENT ORDERS:")
                    for order in orders[:3]:
                        context_parts.append(f"- Order {order.get('order_id', 'N/A')}: {order.get('status', 'unknown')} - ${order.get('total', '0')}")
                    context_parts.append("")
        
        # Add relevant FAQs
        faqs = self.search_faqs(query, limit=2)
        if faqs:
            context_parts.append("RELATED FAQs:")
            for faq in faqs:
                context_parts.append(f"Q: {faq.get('question', 'N/A')}")
                answer = faq.get('answer', 'N/A')
                # Truncate long answers
                if len(answer) > 300:
                    answer = answer[:300] + "..."
                context_parts.append(f"A: {answer}")
                context_parts.append("")
        
        # Add relevant products if query mentions product-related terms
        product_keywords = ['product', 'item', 'device', 'broken', 'not working', 'issue', 'problem']
        if any(kw in query.lower() for kw in product_keywords):
            products = self.search_products(query, limit=1)
            if products:
                context_parts.append("RELEVANT PRODUCT INFO:")
                for prod in products:
                    context_parts.append(f"- Product: {prod.get('name', 'N/A')}")
                    context_parts.append(f"  Common Issues: {prod.get('common_issues', 'N/A')}")
                    context_parts.append(f"  Troubleshooting: {prod.get('troubleshooting_steps', 'N/A')}")
                context_parts.append("")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def get_all_categories(self) -> List[str]:
        """Get all unique categories in the knowledge base."""
        if not self._loaded:
            self.load()
        
        return list(set(entry.get('category', '') for entry in self._knowledge))
    
    def get_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics."""
        if not self._loaded:
            self.load()
        
        return {
            "knowledge_entries": len(self._knowledge),
            "customers": len(self._customers),
            "products": len(self._products),
            "orders": len(self._orders),
            "faqs": len(self._faqs),
        }


# Singleton instance
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """Get the singleton knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
        _knowledge_base.load()
    return _knowledge_base

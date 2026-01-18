"""
Knowledge Base Service

Loads and provides access to the knowledge base CSV files for AI agents.
This enables context-aware responses based on customer, product, and policy data.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class KnowledgeBase:
    """
    In-memory knowledge base loaded from CSV files.
    Provides search and lookup methods for AI agents.
    """
    
    def __init__(self):
        self._knowledge: List[Dict[str, str]] = []
        self._customers: Dict[str, Dict[str, Any]] = {}
        self._products: Dict[str, Dict[str, Any]] = {}
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._faqs: List[Dict[str, Any]] = []
        self._loaded = False
    
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
            self._loaded = True
            logger.info("Knowledge base loaded successfully")
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
    
    # -------------------------------------------------------------------------
    # Search Methods
    # -------------------------------------------------------------------------
    
    def search_solutions(self, query: str, limit: int = 3) -> List[Dict[str, str]]:
        """
        Search knowledge base for relevant solutions.
        Uses keyword matching for simplicity.
        """
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        scored_results = []
        
        for entry in self._knowledge:
            score = 0
            keywords = entry.get('keywords', '').lower().split(',')
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword.strip() in query_lower:
                    score += 2
            
            # Score based on problem text match
            problem = entry.get('problem', '').lower()
            if any(word in problem for word in query_lower.split()):
                score += 1
            
            # Score based on category match
            category = entry.get('category', '').lower()
            if category in query_lower:
                score += 1
            
            if score > 0:
                scored_results.append((score, entry))
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_results[:limit]]
    
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
    
    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search products by name or category."""
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        results = []
        
        for product in self._products.values():
            name = product.get('name', '').lower()
            category = product.get('category', '').lower()
            
            if query_lower in name or query_lower in category:
                results.append(product)
        
        return results
    
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
    
    def search_faqs(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search FAQs by keywords."""
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        scored_results = []
        
        for faq in self._faqs:
            score = 0
            keywords = faq.get('keywords', '').lower().split(',')
            question = faq.get('question', '').lower()
            
            for keyword in keywords:
                if keyword.strip() in query_lower:
                    score += 2
            
            if any(word in question for word in query_lower.split()):
                score += 1
            
            if score > 0:
                scored_results.append((score, faq))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [faq for _, faq in scored_results[:limit]]
    
    # -------------------------------------------------------------------------
    # Context Building for LLM
    # -------------------------------------------------------------------------
    
    def build_context_for_query(self, query: str, customer_id: Optional[str] = None) -> str:
        """
        Build a context string for LLM prompts based on the query.
        Includes relevant solutions, customer info, and FAQs.
        """
        if not self._loaded:
            self.load()
        
        context_parts = []
        
        # Add relevant solutions
        solutions = self.search_solutions(query, limit=2)
        if solutions:
            context_parts.append("RELEVANT KNOWLEDGE BASE ENTRIES:")
            for sol in solutions:
                context_parts.append(f"- Problem: {sol.get('problem', 'N/A')}")
                context_parts.append(f"  Solution: {sol.get('solution', 'N/A')}")
                context_parts.append(f"  Department: {sol.get('department', 'N/A')}")
                context_parts.append(f"  Requires Human: {sol.get('requires_human', 'false')}")
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
                context_parts.append(f"A: {faq.get('answer', 'N/A')[:200]}...")
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

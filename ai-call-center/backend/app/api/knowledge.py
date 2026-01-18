"""
Knowledge Base API

Provides endpoints to explore and search the knowledge base.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.knowledge_base import get_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


# -----------------------------------------------------------------------------
# Response Models
# -----------------------------------------------------------------------------

class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    knowledge_entries: int
    customers: int
    products: int
    orders: int
    faqs: int
    categories: List[str]


class SolutionEntry(BaseModel):
    """A solution entry from the knowledge base."""
    category: str
    subcategory: str
    problem: str
    solution: str
    priority: str
    department: str
    requires_human: bool


class FAQEntry(BaseModel):
    """A FAQ entry."""
    faq_id: str
    question: str
    answer: str
    category: str


class ProductEntry(BaseModel):
    """A product entry."""
    product_id: str
    name: str
    category: str
    price: str
    stock_status: str
    common_issues: str
    troubleshooting_steps: str


class CustomerEntry(BaseModel):
    """A customer entry (sanitized)."""
    customer_id: str
    first_name: str
    last_name: str
    membership_tier: str
    total_orders: str
    loyalty_points: str


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/stats",
    response_model=KnowledgeBaseStats,
    summary="Get Knowledge Base Stats",
)
async def get_stats() -> KnowledgeBaseStats:
    """Get statistics about the knowledge base."""
    kb = get_knowledge_base()
    stats = kb.get_stats()
    categories = kb.get_all_categories()
    
    return KnowledgeBaseStats(
        knowledge_entries=stats["knowledge_entries"],
        customers=stats["customers"],
        products=stats["products"],
        orders=stats["orders"],
        faqs=stats["faqs"],
        categories=categories,
    )


@router.get(
    "/search/solutions",
    response_model=List[SolutionEntry],
    summary="Search Solutions",
)
async def search_solutions(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
) -> List[SolutionEntry]:
    """Search the knowledge base for relevant solutions."""
    kb = get_knowledge_base()
    results = kb.search_solutions(query, limit=limit)
    
    return [
        SolutionEntry(
            category=r.get("category", ""),
            subcategory=r.get("subcategory", ""),
            problem=r.get("problem", ""),
            solution=r.get("solution", ""),
            priority=r.get("priority", ""),
            department=r.get("department", ""),
            requires_human=r.get("requires_human", "false").lower() == "true",
        )
        for r in results
    ]


@router.get(
    "/search/faqs",
    response_model=List[FAQEntry],
    summary="Search FAQs",
)
async def search_faqs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
) -> List[FAQEntry]:
    """Search FAQs by keywords."""
    kb = get_knowledge_base()
    results = kb.search_faqs(query, limit=limit)
    
    return [
        FAQEntry(
            faq_id=r.get("faq_id", ""),
            question=r.get("question", ""),
            answer=r.get("answer", ""),
            category=r.get("category", ""),
        )
        for r in results
    ]


@router.get(
    "/search/products",
    response_model=List[ProductEntry],
    summary="Search Products",
)
async def search_products(
    query: str = Query(..., description="Search query"),
) -> List[ProductEntry]:
    """Search products by name or category."""
    kb = get_knowledge_base()
    results = kb.search_products(query)
    
    return [
        ProductEntry(
            product_id=r.get("product_id", ""),
            name=r.get("name", ""),
            category=r.get("category", ""),
            price=r.get("price", ""),
            stock_status=r.get("stock_status", ""),
            common_issues=r.get("common_issues", ""),
            troubleshooting_steps=r.get("troubleshooting_steps", ""),
        )
        for r in results
    ]


@router.get(
    "/customers/{customer_id}",
    response_model=Optional[CustomerEntry],
    summary="Get Customer Info",
)
async def get_customer(customer_id: str) -> Optional[CustomerEntry]:
    """Get customer information by ID."""
    kb = get_knowledge_base()
    customer = kb.get_customer(customer_id)
    
    if not customer:
        return None
    
    return CustomerEntry(
        customer_id=customer.get("customer_id", ""),
        first_name=customer.get("first_name", ""),
        last_name=customer.get("last_name", ""),
        membership_tier=customer.get("membership_tier", ""),
        total_orders=customer.get("total_orders", ""),
        loyalty_points=customer.get("loyalty_points", ""),
    )


@router.get(
    "/context",
    summary="Build Context for Query",
)
async def build_context(
    query: str = Query(..., description="Customer query"),
    customer_id: Optional[str] = Query(None, description="Optional customer ID"),
) -> dict:
    """
    Build the full context that would be sent to the LLM for a given query.
    Useful for debugging and understanding what context the AI sees.
    """
    kb = get_knowledge_base()
    context = kb.build_context_for_query(query, customer_id)
    
    return {
        "query": query,
        "customer_id": customer_id,
        "context": context,
        "context_length": len(context),
    }

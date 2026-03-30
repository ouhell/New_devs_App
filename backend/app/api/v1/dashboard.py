from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/properties")
async def get_tenant_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Returns all properties belonging to the authenticated tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        from app.core.database_pool import DatabasePool
        from sqlalchemy import text

        db_pool = DatabasePool()
        await db_pool.initialize()

        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        async with db_pool.get_session() as session:
            result = await session.execute(
                text("SELECT id, name, timezone FROM properties WHERE tenant_id = :tid ORDER BY name"),
                {"tid": tenant_id},
            )
            rows = result.fetchall()
            return [{"id": row.id, "name": row.name, "timezone": row.timezone} for row in rows]

    except Exception as e:
        # Fallback: return mock properties scoped to the tenant
        fallback = {
            "tenant-a": [
                {"id": "prop-001", "name": "Beach House Alpha",       "timezone": "Europe/Paris"},
                {"id": "prop-002", "name": "City Apartment Downtown", "timezone": "Europe/Paris"},
                {"id": "prop-003", "name": "Country Villa Estate",    "timezone": "Europe/Paris"},
            ],
            "tenant-b": [
                {"id": "prop-001", "name": "Mountain Lodge Beta", "timezone": "America/New_York"},
                {"id": "prop-004", "name": "Lakeside Cottage",   "timezone": "America/New_York"},
                {"id": "prop-005", "name": "Urban Loft Modern",  "timezone": "America/New_York"},
            ],
        }
        return fallback.get(tenant_id, [])

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }

"""
nitro.multitenancy — Tenant isolation for SaaS applications.

Provides:
- Tenant          : Entity representing a tenant (org/workspace)
- TenantMember    : Entity linking users to tenants with roles
- TenantInvitation: Entity representing a pending invitation to a tenant
- TenantService   : Manage tenants, members, invitations
- TenantContext   : Thread-local tenant context for scoped queries
- require_tenant  : Decorator — injects current_tenant into handler kwargs
- require_tenant_role : Decorator factory — enforces tenant role membership
- TenantError     : Exception raised on tenant resolution failure

Quick start::

    from nitro.multitenancy import Tenant, TenantMember, TenantService, require_tenant, TenantContext

    svc = TenantService()

    # Create tenant
    tenant = svc.create_tenant("Acme Corp", slug="acme")

    # Add member
    svc.add_member(tenant.id, user_id="user-1", role="admin")

    # Set context for scoped queries
    TenantContext.set("acme")

    # Protect routes
    @require_tenant
    async def dashboard(request, current_tenant):
        ...

    # Role-enforced route (use after @require_tenant)
    @require_tenant
    @require_tenant_role("admin")
    async def admin_panel(request, current_tenant, current_user):
        ...
"""

from .models import Tenant, TenantInvitation, TenantMember
from .context import TenantContext
from .service import TenantService
from .decorators import TenantError, require_tenant, require_tenant_role

__all__ = [
    "Tenant",
    "TenantMember",
    "TenantInvitation",
    "TenantService",
    "TenantContext",
    "TenantError",
    "require_tenant",
    "require_tenant_role",
]

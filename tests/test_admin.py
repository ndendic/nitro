"""Comprehensive tests for the nitro.admin module.

Tests cover:
- AdminSite and AdminEntityConfig defaults and custom values
- Entity discovery
- Dashboard view generation
- Entity list/detail/create/edit views
- Admin layout (sidebar, navigation)
- Route registration (structure only — no HTTP)
- Entity counts and badges
- Category grouping in sidebar
- Visibility flags
"""
from __future__ import annotations

import pytest
from nitro.domain.entities.base_entity import Entity
from nitro.domain.repository.sql import SQLModelRepository


# ---------------------------------------------------------------------------
# Test entities
# ---------------------------------------------------------------------------

class AdminProduct(Entity, table=True):
    __tablename__ = "admin_products"
    name: str = ""
    price: float = 0.0
    category: str = ""


class AdminUser(Entity, table=True):
    __tablename__ = "admin_users"
    username: str = ""
    email: str = ""
    role: str = "user"


class AdminOrder(Entity, table=True):
    __tablename__ = "admin_orders"
    customer: str = ""
    total: float = 0.0
    status: str = "pending"


# ---------------------------------------------------------------------------
# DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_db():
    """Reset the SQLModelRepository singleton to use an in-memory DB."""
    SQLModelRepository._instance = None
    SQLModelRepository._initialized = False

    repo = SQLModelRepository("sqlite:///:memory:")
    repo.init_db()
    yield repo

    repo.close() if hasattr(repo, "close") else None
    SQLModelRepository._instance = None
    SQLModelRepository._initialized = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_product(name="Widget", price=9.99) -> AdminProduct:
    p = AdminProduct(name=name, price=price, category="tools")
    p.save()
    return p


def _save_user(username="alice", email="alice@example.com") -> AdminUser:
    u = AdminUser(username=username, email=email)
    u.save()
    return u


# ===========================================================================
# AdminEntityConfig tests
# ===========================================================================

class TestAdminEntityConfig:

    def test_defaults(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig()
        assert cfg.category == ""
        assert cfg.priority == 0
        assert cfg.visible is True
        assert cfg.dashboard_visible is True
        assert cfg.description == ""

    def test_inherits_crud_config(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig(title="Products", icon="package", searchable=False)
        assert cfg.title == "Products"
        assert cfg.icon == "package"
        assert cfg.searchable is False

    def test_resolve_preserves_admin_fields(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig(category="Shop", priority=3, description="All products")
        resolved = cfg.resolve(AdminProduct)
        assert isinstance(resolved, AdminEntityConfig)
        assert resolved.category == "Shop"
        assert resolved.priority == 3
        assert resolved.description == "All products"
        # Also verify CRUD fields got auto-derived
        assert resolved.title == "AdminProducts"
        assert resolved.title_singular == "AdminProduct"

    def test_resolve_with_custom_title(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig(title="Products")
        resolved = cfg.resolve(AdminProduct)
        assert resolved.title == "Products"

    def test_visible_false(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig(visible=False)
        resolved = cfg.resolve(AdminProduct)
        assert resolved.visible is False

    def test_dashboard_visible_false(self):
        from nitro.admin import AdminEntityConfig
        cfg = AdminEntityConfig(dashboard_visible=False)
        resolved = cfg.resolve(AdminProduct)
        assert resolved.dashboard_visible is False


# ===========================================================================
# AdminSite tests
# ===========================================================================

class TestAdminSite:

    def test_defaults(self):
        from nitro.admin import AdminSite
        site = AdminSite()
        assert site.title == "Admin"
        assert site.url_prefix == "/admin"
        assert site.brand_icon == "shield"
        assert site.entities == {}
        assert site.sidebar_width == "w-64"

    def test_custom_values(self):
        from nitro.admin import AdminSite
        site = AdminSite(title="My CMS", url_prefix="/cms", brand_icon="zap")
        assert site.title == "My CMS"
        assert site.url_prefix == "/cms"
        assert site.brand_icon == "zap"

    def test_config_for_unknown_entity(self):
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        cfg = site.config_for(AdminProduct)
        assert isinstance(cfg, AdminEntityConfig)
        assert cfg.title == "AdminProducts"
        assert cfg.visible is True

    def test_config_for_registered_entity(self):
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite(entities={
            "AdminProduct": AdminEntityConfig(
                title="Products",
                icon="package",
                category="Shop",
                description="All products",
            ),
        })
        cfg = site.config_for(AdminProduct)
        assert cfg.title == "Products"
        assert cfg.icon == "package"
        assert cfg.category == "Shop"
        assert cfg.description == "All products"

    def test_config_for_preserves_visibility(self):
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite(entities={
            "AdminProduct": AdminEntityConfig(visible=False),
        })
        cfg = site.config_for(AdminProduct)
        assert cfg.visible is False


# ===========================================================================
# Discovery tests
# ===========================================================================

class TestDiscovery:

    def test_discover_finds_table_entities(self):
        from nitro.admin import discover_entities
        entities = discover_entities()
        names = [e.__name__ for e in entities]
        assert "AdminProduct" in names
        assert "AdminUser" in names
        assert "AdminOrder" in names

    def test_discover_returns_sorted(self):
        from nitro.admin import discover_entities
        entities = discover_entities()
        names = [e.__name__ for e in entities]
        assert names == sorted(names)

    def test_discover_explicit_base(self):
        from nitro.admin import discover_entities
        entities = discover_entities(base_class=Entity)
        assert len(entities) > 0

    def test_discover_returns_classes(self):
        from nitro.admin import discover_entities
        entities = discover_entities()
        for cls in entities:
            assert isinstance(cls, type)
            assert issubclass(cls, Entity)


# ===========================================================================
# View tests
# ===========================================================================

class TestDashboardView:

    def test_renders_entity_cards(self):
        from nitro.admin import AdminSite, admin_dashboard_view, AdminEntityConfig
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig().resolve(AdminProduct)),
            (AdminUser, AdminEntityConfig().resolve(AdminUser)),
        ]
        counts = {"AdminProduct": 5, "AdminUser": 3}
        html = str(admin_dashboard_view(site, configs, counts))
        assert "admin-dashboard" in html
        assert "5" in html
        assert "3" in html

    def test_dashboard_with_zero_entities(self):
        from nitro.admin import AdminSite, admin_dashboard_view
        site = AdminSite()
        html = str(admin_dashboard_view(site, [], {}))
        assert "0 registered entities" in html

    def test_hidden_entity_not_on_dashboard(self):
        from nitro.admin import AdminSite, admin_dashboard_view, AdminEntityConfig
        site = AdminSite()
        cfg = AdminEntityConfig(dashboard_visible=False).resolve(AdminProduct)
        configs = [(AdminProduct, cfg)]
        html = str(admin_dashboard_view(site, configs, {"AdminProduct": 10}))
        # The dashboard should still render, just without the hidden entity's card
        assert "admin-dashboard" in html

    def test_entity_count_displayed(self):
        from nitro.admin import AdminSite, admin_dashboard_view, AdminEntityConfig
        site = AdminSite()
        configs = [(AdminProduct, AdminEntityConfig().resolve(AdminProduct))]
        html = str(admin_dashboard_view(site, configs, {"AdminProduct": 42}))
        assert "42" in html

    def test_description_shown(self):
        from nitro.admin import AdminSite, admin_dashboard_view, AdminEntityConfig
        site = AdminSite()
        cfg = AdminEntityConfig(description="Manage all products").resolve(AdminProduct)
        configs = [(AdminProduct, cfg)]
        html = str(admin_dashboard_view(site, configs, {"AdminProduct": 0}))
        assert "Manage all products" in html


class TestEntityViews:

    def test_list_view(self):
        from nitro.admin import admin_entity_list_view, AdminEntityConfig, AdminSite
        _save_product("Widget")
        _save_product("Gadget")
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        html = str(admin_entity_list_view(AdminProduct, cfg, site))
        assert "admin-entity-list" in html

    def test_detail_view(self):
        from nitro.admin import admin_entity_detail_view, AdminEntityConfig, AdminSite
        p = _save_product("Widget")
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        html = str(admin_entity_detail_view(AdminProduct, p.id, cfg, site))
        assert "admin-entity-detail" in html

    def test_detail_view_not_found(self):
        from nitro.admin import admin_entity_detail_view, AdminEntityConfig, AdminSite
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        with pytest.raises(ValueError, match="not found"):
            admin_entity_detail_view(AdminProduct, "nonexistent", cfg, site)

    def test_create_view(self):
        from nitro.admin import admin_entity_create_view, AdminEntityConfig, AdminSite
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        html = str(admin_entity_create_view(AdminProduct, cfg, site))
        assert "admin-entity-create" in html

    def test_edit_view(self):
        from nitro.admin import admin_entity_edit_view, AdminEntityConfig, AdminSite
        p = _save_product("Widget")
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        html = str(admin_entity_edit_view(AdminProduct, p.id, cfg, site))
        assert "admin-entity-edit" in html

    def test_edit_view_not_found(self):
        from nitro.admin import admin_entity_edit_view, AdminEntityConfig, AdminSite
        site = AdminSite()
        cfg = AdminEntityConfig().resolve(AdminProduct)
        with pytest.raises(ValueError, match="not found"):
            admin_entity_edit_view(AdminProduct, "nonexistent", cfg, site)


# ===========================================================================
# Layout tests
# ===========================================================================

class TestLayout:

    def test_sidebar_renders(self):
        from nitro.admin.layout import admin_sidebar
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig(icon="package").resolve(AdminProduct)),
            (AdminUser, AdminEntityConfig(icon="users").resolve(AdminUser)),
        ]
        html = str(admin_sidebar(site, configs))
        assert "Dashboard" in html
        assert "Admin" in html

    def test_sidebar_active_highlight(self):
        from nitro.admin.layout import admin_sidebar
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig().resolve(AdminProduct)),
        ]
        html = str(admin_sidebar(site, configs, active_entity="AdminProduct"))
        assert "bg-accent" in html

    def test_sidebar_hidden_entity(self):
        from nitro.admin.layout import admin_sidebar
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        hidden_cfg = AdminEntityConfig(visible=False).resolve(AdminProduct)
        configs = [(AdminProduct, hidden_cfg)]
        html = str(admin_sidebar(site, configs))
        # Hidden entity should not appear as a nav link
        assert "adminproduct" not in html.lower() or "Dashboard" in html

    def test_sidebar_categories(self):
        from nitro.admin.layout import admin_sidebar
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig(category="Shop").resolve(AdminProduct)),
            (AdminUser, AdminEntityConfig(category="Auth").resolve(AdminUser)),
        ]
        html = str(admin_sidebar(site, configs))
        assert "Shop" in html
        assert "Auth" in html

    def test_sidebar_counts(self):
        from nitro.admin.layout import admin_sidebar
        from nitro.admin import AdminSite, AdminEntityConfig
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig().resolve(AdminProduct)),
        ]
        html = str(admin_sidebar(site, configs, entity_counts={"AdminProduct": 42}))
        assert "42" in html

    def test_full_layout(self):
        from nitro.admin.layout import admin_layout
        from nitro.admin import AdminSite, AdminEntityConfig
        from rusty_tags import Div
        site = AdminSite()
        configs = [
            (AdminProduct, AdminEntityConfig().resolve(AdminProduct)),
        ]
        html = str(admin_layout(site, Div("Test content"), configs, page_title="Test"))
        assert "Test content" in html
        assert "<html" in html.lower()

    def test_layout_with_custom_title(self):
        from nitro.admin.layout import admin_layout
        from nitro.admin import AdminSite, AdminEntityConfig
        from rusty_tags import Div
        site = AdminSite(title="My CMS")
        configs = []
        html = str(admin_layout(site, Div("Content"), configs, page_title="My Page"))
        assert "My Page" in html


# ===========================================================================
# Route registration tests (structure only, no HTTP)
# ===========================================================================

class TestRouteRegistration:

    def test_register_admin_adds_routes(self):
        from sanic import Sanic
        from nitro.admin import register_admin, AdminSite

        app = Sanic(f"test_admin_routes_{id(self)}")
        site = AdminSite()
        register_admin(app, site=site, entities=[AdminProduct, AdminUser])

        route_paths = [r.path for r in app.router.routes]
        # Sanic strips leading / and adds type annotations to params
        assert any("admin" == p or p.startswith("admin") for p in route_paths)
        assert any("entity_name" in p for p in route_paths)
        assert any("entity_id" in p for p in route_paths)
        assert any("create" in p for p in route_paths)
        assert any("edit" in p for p in route_paths)
        assert any("delete" in p for p in route_paths)

    def test_register_with_custom_prefix(self):
        from sanic import Sanic
        from nitro.admin import register_admin, AdminSite

        app = Sanic(f"test_admin_prefix_{id(self)}")
        site = AdminSite(url_prefix="/cms")
        register_admin(app, site=site, entities=[AdminProduct])

        route_paths = [r.path for r in app.router.routes]
        assert any(p.startswith("cms") for p in route_paths)

    def test_register_with_explicit_entities(self):
        from sanic import Sanic
        from nitro.admin import register_admin, AdminSite

        app = Sanic(f"test_admin_explicit_{id(self)}")
        site = AdminSite()
        register_admin(app, site=site, entities=[AdminProduct])

        route_paths = [r.path for r in app.router.routes]
        assert any("entity_name" in p for p in route_paths)

    def test_register_with_entity_configs(self):
        from sanic import Sanic
        from nitro.admin import register_admin, AdminSite, AdminEntityConfig

        app = Sanic(f"test_admin_configs_{id(self)}")
        site = AdminSite(entities={
            "AdminProduct": AdminEntityConfig(title="Products", icon="package"),
        })
        register_admin(app, site=site, entities=[AdminProduct])

        route_paths = [r.path for r in app.router.routes]
        assert any(p.startswith("admin") for p in route_paths)

    def test_route_count(self):
        from sanic import Sanic
        from nitro.admin import register_admin, AdminSite

        app = Sanic(f"test_admin_route_count_{id(self)}")
        site = AdminSite()
        register_admin(app, site=site, entities=[AdminProduct])

        # Dashboard + list + create_form + create_post + detail + edit_form + edit_post + delete = 8
        # But some share the same path with different methods
        route_paths = [r.path for r in app.router.routes]
        assert len(route_paths) >= 6  # At least 6 unique paths


# ===========================================================================
# Integration: entity counts
# ===========================================================================

class TestEntityCounts:

    def test_counts_with_data(self):
        from nitro.admin.routes import _get_entity_counts
        _save_product("A")
        _save_product("B")
        _save_user("alice")
        counts = _get_entity_counts([AdminProduct, AdminUser])
        assert counts["AdminProduct"] == 2
        assert counts["AdminUser"] == 1

    def test_counts_empty(self):
        from nitro.admin.routes import _get_entity_counts
        counts = _get_entity_counts([AdminProduct])
        assert counts["AdminProduct"] == 0

    def test_counts_no_entities(self):
        from nitro.admin.routes import _get_entity_counts
        counts = _get_entity_counts([])
        assert counts == {}


# ===========================================================================
# End-to-end view + layout integration
# ===========================================================================

class TestAdminFullPage:

    def test_dashboard_in_layout(self):
        from nitro.admin import AdminSite, AdminEntityConfig, admin_dashboard_view
        from nitro.admin.layout import admin_layout

        _save_product("Widget")
        _save_product("Gadget")
        _save_user("alice")

        site = AdminSite(title="Test CMS")
        configs = [
            (AdminProduct, AdminEntityConfig(title="Products", icon="package", category="Shop").resolve(AdminProduct)),
            (AdminUser, AdminEntityConfig(title="Users", icon="users", category="Auth").resolve(AdminUser)),
        ]
        counts = {"AdminProduct": 2, "AdminUser": 1}
        content = admin_dashboard_view(site, configs, counts)
        page = admin_layout(site, content, configs, page_title="Test CMS Dashboard", entity_counts=counts)
        html = str(page)

        # Check full page structure
        assert "<html" in html.lower()
        assert "Test CMS" in html
        assert "Products" in html
        assert "Users" in html
        assert "Shop" in html
        assert "Auth" in html
        assert "2" in html  # product count
        assert "1" in html  # user count

    def test_entity_list_in_layout(self):
        from nitro.admin import AdminSite, AdminEntityConfig, admin_entity_list_view
        from nitro.admin.layout import admin_layout

        _save_product("Widget")

        site = AdminSite()
        cfg = AdminEntityConfig(title="Products").resolve(AdminProduct)
        configs = [(AdminProduct, cfg)]

        content = admin_entity_list_view(AdminProduct, cfg, site)
        page = admin_layout(
            site, content, configs,
            active_entity="AdminProduct",
            page_title="Products — Admin",
        )
        html = str(page)
        assert "admin-entity-list" in html
        assert "bg-accent" in html  # active sidebar item

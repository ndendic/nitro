# Nitro Framework - Roadmap & Milestones

**Version:** 1.0  
**Planning Horizon:** 18 months (Q1 2025 - Q2 2026)  
**Team Size Assumption:** 1-2 developers  
**Last Updated:** January 2025

---

## Overview

This roadmap transforms Nitro from a templating toolkit into a full-stack framework by merging proven patterns from StarModel while maintaining RustyTags' performance foundation. We build incrementally, shipping value at every milestone, with each phase standing independently.

**Key Principles:**
- ✅ **Ship early, ship often** - Each milestone is usable
- ✅ **No big-bang rewrites** - Backward compatibility where possible
- ✅ **Learning gates** - Validate before proceeding
- ✅ **Community-first** - Engage users at every phase

---

## Timeline Visualization

```
2025 Q1         Q2              Q3              Q4         2026 Q1
|---------------|---------------|---------------|---------------|
   Phase 0          Phase 1          Phase 2         Phase 3    Phase 4
   Prep &        Foundation      Auto-Magic     Enterprise  Production
   Planning      (4-6 weeks)    (6-8 weeks)    (8-10 wks)  (Ongoing)
```

---

## Phase 0: Preparation & Architecture Validation
**Timeline:** 2 weeks (Immediate)  
**Status:** CURRENT PHASE  
**Goal:** Validate merge strategy and establish development environment

### Milestone 0.1: Development Environment Setup
**Duration:** 3 days

**Deliverables:**
- [ ] Single shared venv in ecosystem root
- [ ] `setup-dev.sh` script working
- [ ] VSCode workspace configured
- [ ] All 3 projects (RustyTags, Nitro, StarModel) installed editable
- [ ] Playground directory with test apps

**Success Criteria:**
- Can modify RustyTags Rust code → `maturin develop` → immediately available in Nitro
- Can modify Nitro Python code → immediately available in playground
- Can run tests across all projects

**Risks & Mitigation:**
- **Risk:** Dependency conflicts between projects
- **Mitigation:** Use minimal dependencies, lock versions in pyproject.toml

---

### Milestone 0.2: Architecture Documentation
**Duration:** 4 days

**Deliverables:**
- [x] **Vision Document** - Overall project intent (COMPLETED)
- [ ] **API Design Document** - Entity/SQLEntity interface specification
- [ ] **Migration Plan** - Detailed StarModel → Nitro mapping

**Success Criteria:**
- Team consensus on entity API surface
- Clear decision on event system terminology (@event vs @action)
- Documented trade-offs for deferred features

**Key Decisions to Finalize:**
1. ✅ Entity base class API (rich domain model - decided)
2. ⚠️ Signal descriptor syntax (defer to Phase 2 - tentative)
3. ⚠️ @event decorator naming (@action? @route? - needs decision)
4. ✅ File structure (flat nitro/ vs nested nitro/core/ - prefer flat)

---

### Milestone 0.3: Proof-of-Concept Spike
**Duration:** 3 days

**Deliverables:**
- [ ] Minimal Entity class with MemoryRepo
- [ ] SQLEntity class with SQLModelBackend  
- [ ] Working counter example (manual routing)
- [ ] Working todo example (manual routing with SQLEntity)

**Success Criteria:**
- Counter works with FastAPI + MemoryRepo
- Todo app works with FastAPI + SQLModelBackend
- Both examples < 50 lines each
- Can swap MemoryRepo ↔ SQLModelBackend in 1 line

**Exit Gate:**
- ❌ If POC fails → revisit architecture
- ✅ If POC succeeds → proceed to Phase 1

---

## Phase 1: Foundation - Rich Entities + Hybrid Persistence
**Timeline:** 4-6 weeks (Late Q1 2025)  
**Goal:** Merge StarModel's persistence layer and entity system without routing magic

### Milestone 1.1: Persistence Layer Migration
**Duration:** 1.5 weeks

**Deliverables:**
- [ ] Copy `starmodel/persistence/` → `nitro/persistence/`
  - [ ] `base.py` - EntityPersistenceBackend interface
  - [ ] `memory.py` - MemoryRepo implementation
  - [ ] `sql.py` - SQLModelBackend implementation
- [ ] Adapt imports and naming to Nitro conventions
- [ ] Add comprehensive tests (90%+ coverage)
- [ ] Documentation for persistence backends

**Success Criteria:**
- All tests pass
- MemoryRepo singleton works correctly
- SQLModelBackend can save/load/delete entities
- TTL cleanup works for MemoryRepo
- API documentation complete

**Technical Debt:**
- DatastarRepo and RedisRepo deferred to Phase 2
- Async persistence methods deferred to Phase 2

---

### Milestone 1.2: Entity Base Classes
**Duration:** 1.5 weeks

**Deliverables:**
- [ ] Create `nitro/entity.py`
  - [ ] Entity class (Pydantic BaseModel)
  - [ ] Persistence methods (save, delete, exists, get)
  - [ ] Signal support for Datastar (basic)
  - [ ] Configuration via class attributes
- [ ] Create `nitro/entity_sql.py`
  - [ ] SQLEntity class (SQLModel integration)
  - [ ] All CRUD methods (all, search, filter)
  - [ ] Table creation support
- [ ] Comprehensive unit tests
- [ ] API reference documentation

**Success Criteria:**
- Can define entities with business logic methods
- Entity.save() works with configured backend
- SQLEntity.all() returns all records
- SQLEntity.filter() supports common query patterns
- Signals work for Datastar integration
- 100% test coverage on public API

**API Surface (Locked):**
```python
# This is the contract we're committing to
class Entity(BaseModel):
    id: str
    _persistence_backend_class = MemoryRepo
    
    def save(self, ttl: Optional[int] = None) -> bool: ...
    def delete(self) -> bool: ...
    def exists(self) -> bool: ...
    
    @classmethod
    def get(cls, entity_id: str) -> Optional['Entity']: ...
    
    @property
    def signals(self) -> Dict[str, Any]: ...

class SQLEntity(SQLModel, table=True):
    id: str = Field(primary_key=True)
    
    # All Entity methods plus:
    @classmethod
    def all(cls) -> List['SQLEntity']: ...
    
    @classmethod
    def filter(cls, **kwargs) -> List['SQLEntity']: ...
    
    @classmethod
    def search(cls, search_value: str, ...) -> List: ...
```

---

### Milestone 1.3: Integration & Examples
**Duration:** 1 week

**Deliverables:**
- [ ] **Example 1:** Counter app (FastAPI + MemoryRepo)
- [ ] **Example 2:** Todo app (FastAPI + SQLModelBackend)
- [ ] **Example 3:** Order system (Flask + domain events)
- [ ] **Example 4:** Blog (FastHTML + SQLEntity)
- [ ] Integration tests for each framework
- [ ] Tutorial documentation for each example

**Success Criteria:**
- All 4 examples work and are documented
- Each example demonstrates different features:
  - Counter: In-memory, basic CRUD
  - Todo: SQL persistence, filtering
  - Order: Domain events, business logic
  - Blog: FastHTML integration, real-time updates
- Examples run on fresh install

**User Testing:**
- [ ] Share with 3-5 Python developers for feedback
- [ ] Measure "time to first working app"
- [ ] Collect feedback on API intuitiveness

---

### Milestone 1.4: Documentation & Release
**Duration:** 1 week

**Deliverables:**
- [ ] Getting Started guide
- [ ] Tutorial series (4 examples above)
- [ ] API Reference (complete)
- [ ] Architecture documentation
- [ ] Migration guide (if breaking changes)
- [ ] CHANGELOG.md
- [ ] Release blog post

**Success Criteria:**
- Complete documentation published
- PyPI package published (nitro v1.0.0)
- Announcement on Python forums/Reddit/HN
- GitHub repo organized with issues/discussions enabled

**Phase 1 Exit Criteria:**
✅ Can build todo app in < 50 lines  
✅ Can swap persistence backend in 1 line  
✅ At least 10 GitHub stars (validation)  
✅ No critical bugs reported in 2 weeks  
✅ Documentation is clear (measured by user questions)  

---

## Phase 2: Auto-Magic - Routing & CRUD Generation
**Timeline:** 6-8 weeks (Q2 2025)  
**Goal:** Reduce boilerplate with auto-routing and generated admin UI

### Milestone 2.1: @action Decorator Design
**Duration:** 1 week (design-heavy)

**Deliverables:**
- [ ] Design document for auto-routing system
- [ ] Decision on decorator naming (@action, @route, or @event)
- [ ] Signature specification for route generation
- [ ] Parameter extraction strategy (Datastar payload + FastAPI params)
- [ ] Conflict resolution (multiple entities with same method names)

**Key Design Questions:**
1. Should it be `@action` or `@event`? (avoid confusion with Blinker events)
2. How to handle method parameters? (automatic Datastar extraction)
3. How to generate URLs? (`/entity_name/method_name` or custom?)
4. How to handle HTTP methods? (GET, POST, PUT, DELETE)
5. How to support different frameworks? (FastAPI vs Flask vs FastHTML)

**Success Criteria:**
- Design reviewed by at least 2 external developers
- All edge cases documented
- Framework adapter interface specified

**Research Tasks:**
- [ ] Review FastHTML's FT decorator pattern
- [ ] Review Django's URL routing
- [ ] Review Rails' resourceful routing
- [ ] Survey users: which syntax feels most natural?

---

### Milestone 2.2: Framework Dispatcher System
**Duration:** 2 weeks

**Deliverables:**
- [ ] Create `nitro/app/dispatcher.py`
  - [ ] Base Dispatcher class (framework-agnostic)
  - [ ] Route registration logic
  - [ ] URL generation
  - [ ] Parameter extraction
- [ ] Create `nitro/adapters/fastapi.py`
  - [ ] FastAPIDispatcher
  - [ ] `configure_app()` function
- [ ] Create `nitro/adapters/fasthtml.py`
  - [ ] FastHTMLDispatcher  
  - [ ] `configure_app()` function
- [ ] Create `nitro/adapters/flask.py`
  - [ ] FlaskDispatcher
  - [ ] `configure_app()` function

**Success Criteria:**
- Can register all entities with 1 function call
- Routes are generated correctly for each framework
- Parameters extract from both URL and Datastar payload
- SSE responses work for real-time updates

**API Example:**
```python
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_app

app = FastAPI()
configure_app(app)  # Auto-registers all entities
```

---

### Milestone 2.3: @action Decorator Implementation
**Duration:** 2 weeks

**Deliverables:**
- [ ] Implement `@action` decorator (or chosen name)
- [ ] EventInfo metadata class
- [ ] EventMethodDescriptor for URL generation
- [ ] Signal descriptors (Entity.field_signal)
- [ ] Comprehensive tests
- [ ] Documentation with examples

**Success Criteria:**
- Can decorate entity methods with `@action`
- Routes are auto-generated when `configure_app()` is called
- Can generate Datastar URLs: `Counter.increment()`
- Signal descriptors work: `Counter.count_signal` → `"$Counter.count"`
- Works with all 3 framework adapters

**Example Usage:**
```python
class Counter(Entity):
    count: int = 0
    
    @action(method="POST")
    def increment(self, amount: int = 1):
        self.count += amount
        self.save()

# In routes:
Button("+1", data_on_click=Counter.increment(1))
Span(data_text=Counter.count_signal)
```

---

### Milestone 2.4: Additional Persistence Backends
**Duration:** 2 weeks

**Deliverables:**
- [ ] **RedisRepo** implementation
  - [ ] Save/load/delete with TTL
  - [ ] Connection pooling
  - [ ] Serialization strategy
  - [ ] Tests with real Redis (docker-compose)
- [ ] **DatastarRepo** implementation (client-side storage)
  - [ ] localStorage/sessionStorage integration
  - [ ] Automatic sync with server
  - [ ] Conflict resolution strategy
- [ ] Documentation for both backends

**Success Criteria:**
- RedisRepo works with redis-py
- Can cache entities in Redis with TTL
- DatastarRepo stores entities in browser storage
- Examples demonstrate each backend
- Performance benchmarks documented

---

### Milestone 2.5: Auto-Generated CRUD UI
**Duration:** 2 weeks

**Deliverables:**
- [ ] Create `nitro/admin/` module
- [ ] Table component generator from SQLEntity
  - [ ] Column detection from model fields
  - [ ] Sorting, filtering, pagination
  - [ ] RustyTags-based rendering
- [ ] Form generator from entity schema
  - [ ] Input types from field annotations
  - [ ] Validation from Pydantic
  - [ ] Create/Edit/Delete actions
- [ ] Admin registration API
- [ ] Customization hooks

**Success Criteria:**
- Can register an entity: `admin.register(Product)`
- Auto-generates table view at `/admin/product`
- Auto-generates forms for create/edit
- Supports basic CRUD without any custom code
- Can customize columns, filters, actions

**API Example:**
```python
from nitro.admin import admin

class Product(SQLEntity, table=True):
    name: str
    price: float
    stock: int

# Auto-generates admin UI
admin.register(Product, 
    list_display=['name', 'price', 'stock'],
    list_filter=['price'],
    search_fields=['name']
)
```

---

### Milestone 2.6: Phase 2 Documentation & Release
**Duration:** 1 week

**Deliverables:**
- [ ] Update all examples to use @action
- [ ] Tutorial on auto-routing
- [ ] Tutorial on admin UI
- [ ] Video walkthrough (15 minutes)
- [ ] Release blog post
- [ ] CHANGELOG.md update

**Phase 2 Exit Criteria:**
✅ Can build CRUD app with admin in < 20 lines  
✅ @action decorator works with 3+ frameworks  
✅ Admin UI generates without custom code  
✅ At least 50 GitHub stars  
✅ At least 3 community examples shared  
✅ No critical bugs in 2 weeks  

**Decision Point:**
- ❓ Is the @action pattern intuitive? (measure via user feedback)
- ❓ Should we continue with Phase 3 or iterate on Phase 2?
- ❓ What features are users requesting most?

---

## Phase 3: Enterprise - Application Service Layer
**Timeline:** 8-10 weeks (Q3 2025)  
**Goal:** Add CQRS patterns, transaction management, and async event processing

### Milestone 3.1: Command/Query Separation
**Duration:** 2 weeks

**Deliverables:**
- [ ] Design document for CQRS patterns
- [ ] Command base class
- [ ] Query base class
- [ ] CommandHandler interface
- [ ] QueryHandler interface
- [ ] Registration system
- [ ] Examples demonstrating pattern

**Success Criteria:**
- Can separate commands (writes) from queries (reads)
- Handlers are testable in isolation
- Optional pattern - entities still work without it
- Documentation explains when to use CQRS

**Example Usage:**
```python
# Command (mutation)
class PlaceOrderCommand:
    order_id: str
    items: List[Item]

class PlaceOrderHandler:
    def handle(self, cmd: PlaceOrderCommand):
        order = Order.get(cmd.order_id)
        order.place(cmd.items)
        order.save()
        order_placed.send(order)

# Query (read)
class GetOrderQuery:
    order_id: str

class GetOrderHandler:
    def handle(self, query: GetOrderQuery):
        return Order.get(query.order_id)
```

---

### Milestone 3.2: Unit of Work Pattern
**Duration:** 2 weeks

**Deliverables:**
- [ ] Create `nitro/app/uow.py`
- [ ] UnitOfWork context manager
- [ ] Transaction boundary support
- [ ] Rollback on exception
- [ ] Integration with SQLModelBackend
- [ ] Tests with multiple entity changes

**Success Criteria:**
- Can wrap multiple operations in transaction
- Rollback works correctly on errors
- Nested UoW supported
- Works with async/await

**Example Usage:**
```python
async with UnitOfWork() as uow:
    order = Order.get(order_id)
    order.place()
    await uow.orders.save(order)
    
    for item in order.items:
        product = Product.get(item.product_id)
        product.reduce_stock(item.quantity)
        await uow.products.save(product)
    
    await uow.commit()  # All or nothing
```

---

### Milestone 3.3: Event Bus & Async Processing
**Duration:** 2 weeks

**Deliverables:**
- [ ] Create `nitro/app/bus.py`
- [ ] InProcessBus for synchronous events
- [ ] AsyncBus for background processing
- [ ] Integration with Blinker signals
- [ ] Celery adapter (optional)
- [ ] Dramatiq adapter (optional)

**Success Criteria:**
- Domain events can process asynchronously
- Can queue events for background workers
- Error handling and retry logic
- Monitoring/observability hooks

**Example Usage:**
```python
# Synchronous (immediate)
order_placed.send(order)

# Asynchronous (background)
async_bus.publish(OrderPlacedEvent(order_id=order.id))

# Celery integration
@celery_task
@on(order_placed)
def send_confirmation_email(order):
    EmailService.send(order.customer_email, "Order confirmed")
```

---

### Milestone 3.4: Repository Pattern Formalization
**Duration:** 1 week

**Deliverables:**
- [ ] Abstract Repository interface
- [ ] SQLRepository implementation
- [ ] MemoryRepository implementation
- [ ] RedisRepository implementation
- [ ] Repository registration system
- [ ] Dependency injection for repositories

**Success Criteria:**
- Repositories are swappable via configuration
- Tests can use MemoryRepository
- Production uses SQLRepository
- Clean separation from entity classes

---

### Milestone 3.5: Advanced Query Patterns
**Duration:** 2 weeks

**Deliverables:**
- [ ] Query builder API
- [ ] Specification pattern
- [ ] Complex filtering (AND/OR/NOT)
- [ ] Joins and eager loading
- [ ] Pagination helpers
- [ ] Performance optimizations

**Success Criteria:**
- Can express complex queries fluently
- Avoid N+1 query problems
- Works with SQLModelBackend
- Documentation with examples

**Example Usage:**
```python
# Complex query
products = Product.query()
    .where(Product.price < 100)
    .where(Product.stock > 0)
    .join(Category, Product.category_id == Category.id)
    .order_by(Product.created_at.desc())
    .limit(20)
    .all()

# Specification pattern
class InStockSpec:
    def is_satisfied_by(self, product):
        return product.stock > 0

class AffordableSpec:
    def __init__(self, max_price):
        self.max_price = max_price
    
    def is_satisfied_by(self, product):
        return product.price <= self.max_price

products = Product.filter(
    InStockSpec() & AffordableSpec(100)
)
```

---

### Milestone 3.6: Phase 3 Documentation & Release
**Duration:** 1 week

**Deliverables:**
- [ ] CQRS pattern guide
- [ ] UnitOfWork tutorial
- [ ] Event Bus documentation
- [ ] Repository pattern guide
- [ ] Migration guide from Phase 2
- [ ] Release blog post

**Phase 3 Exit Criteria:**
✅ CQRS pattern works for complex domains  
✅ UnitOfWork manages transactions correctly  
✅ Async event processing works  
✅ At least 100 GitHub stars  
✅ At least 1 production deployment reported  
✅ No critical bugs in 3 weeks  

---

## Phase 4: Production - Scaling & Ecosystem
**Timeline:** Ongoing (Q4 2025 - Q2 2026)  
**Goal:** Production-ready features, multi-instance sync, plugin system

### Milestone 4.1: Multi-Instance Coordination
**Duration:** 3 weeks

**Deliverables:**
- [ ] Redis pub/sub for entity sync
- [ ] Distributed cache invalidation
- [ ] Session affinity handling
- [ ] Conflict resolution strategies
- [ ] Performance benchmarks

**Success Criteria:**
- 3-node deployment syncs in real-time
- SSE events broadcast across instances
- Cache remains consistent
- No split-brain scenarios

---

### Milestone 4.2: Background Job Integration
**Duration:** 2 weeks

**Deliverables:**
- [ ] Celery integration
- [ ] Dramatiq integration
- [ ] RQ integration
- [ ] Job retry policies
- [ ] Monitoring/observability

**Success Criteria:**
- Can queue domain events as background jobs
- Retry logic works correctly
- Dead letter queue handling
- Job dashboard available

---

### Milestone 4.3: CLI Tooling
**Duration:** 2 weeks

**Deliverables:**
- [ ] `nitro` CLI command
- [ ] `nitro init` - project scaffolding
- [ ] `nitro migrate` - database migrations
- [ ] `nitro generate entity` - code generation
- [ ] `nitro dev` - development server
- [ ] `nitro test` - test runner

**Success Criteria:**
- Can scaffold new project in < 1 minute
- Migrations work with Alembic
- Code generation is useful
- CLI is well-documented

---

### Milestone 4.4: Plugin System
**Duration:** 3 weeks

**Deliverables:**
- [ ] Plugin discovery via entry points
- [ ] Plugin registration API
- [ ] Official plugins:
  - [ ] Authentication (JWT, OAuth, Azure AD)
  - [ ] Authorization (RBAC, permissions)
  - [ ] Audit logging
  - [ ] API documentation (OpenAPI)
- [ ] Plugin development guide

**Success Criteria:**
- Third-party plugins can extend Nitro
- Official plugins are production-ready
- Plugin ecosystem has 5+ community plugins

---

### Milestone 4.5: Observability & Monitoring
**Duration:** 2 weeks

**Deliverables:**
- [ ] Structured logging
- [ ] Metrics (Prometheus)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Health check endpoints
- [ ] Performance profiling

**Success Criteria:**
- Can monitor Nitro apps in production
- Metrics exported to standard tools
- Traces work across services
- Health checks are reliable

---

### Milestone 4.6: WebSocket Support
**Duration:** 2 weeks

**Deliverables:**
- [ ] WebSocket adapter alongside SSE
- [ ] Bidirectional entity sync
- [ ] Connection management
- [ ] Scalability testing

**Success Criteria:**
- Can use WebSocket instead of SSE
- Supports 10k+ concurrent connections
- Works with multi-instance setup

---

## Continuous Tracks (All Phases)

### Documentation Track
**Ongoing throughout all phases**

**Deliverables (per phase):**
- [ ] API reference (auto-generated from docstrings)
- [ ] Tutorial updates
- [ ] Example applications
- [ ] Blog posts
- [ ] Video content
- [ ] Migration guides

**Success Metrics:**
- Documentation scores high on user surveys
- < 5 minutes to find answers in docs
- Code examples always work

---

### Community Track
**Ongoing throughout all phases**

**Deliverables:**
- [ ] GitHub discussions enabled
- [ ] Discord server created
- [ ] Weekly office hours (optional)
- [ ] Monthly newsletter
- [ ] Conference talks (PyCon, EuroPython)
- [ ] Plugin showcase

**Success Metrics:**
- 500+ GitHub stars by end of Phase 3
- 100+ Discord members by end of Phase 3
- 10+ community-contributed examples
- 5+ third-party plugins

---

### Testing Track
**Ongoing throughout all phases**

**Standards:**
- Unit tests: 90%+ coverage
- Integration tests: All framework adapters
- E2E tests: All example applications
- Performance tests: Regression detection
- Security tests: OWASP checks

---

## Risk Management

### High-Risk Items

**Risk 1: Adoption resistance**
- **Mitigation:** Focus on incremental adoption, works with existing frameworks
- **Contingency:** Pivot messaging based on early user feedback
- **Decision point:** After Phase 1, if < 10 stars in 4 weeks

**Risk 2: Performance issues**
- **Mitigation:** Benchmark early and often, RustyTags provides fast foundation
- **Contingency:** Optimize hot paths, add caching layers
- **Decision point:** If performance < 2x pure FastAPI/Flask

**Risk 3: API complexity**
- **Mitigation:** User testing at every milestone, iterate on feedback
- **Contingency:** Simplify API, add convenience functions
- **Decision point:** If "time to first app" > 15 minutes

**Risk 4: Scope creep**
- **Mitigation:** Strict milestone exit criteria, defer features aggressively
- **Contingency:** Cut features to maintain schedule
- **Decision point:** If phase takes >1.5x estimated time

---

## Success Metrics

### Phase 1 (Foundation)
- ⏱️ Time to first working app: < 5 minutes
- 📝 Todo app: < 50 lines of code
- ⭐ GitHub stars: 10+
- 👥 Early adopters: 3-5 developers testing
- 🐛 Critical bugs: 0 in 2 weeks
- 📚 Documentation: Complete API reference

### Phase 2 (Auto-Magic)
- ⏱️ Time to CRUD with admin: < 15 minutes
- 📝 CRUD app: < 20 lines of code
- ⭐ GitHub stars: 50+
- 👥 Community examples: 3+
- 🔌 Framework support: 3+ (FastAPI, Flask, FastHTML)
- 📊 User satisfaction: > 80% (survey)

### Phase 3 (Enterprise)
- 🏢 Production deployments: 1+
- ⭐ GitHub stars: 100+
- 👥 Community plugins: 2+
- 🎯 Feature completeness: CQRS + UoW working
- 📈 Performance: < 10ms overhead per request
- 🧪 Test coverage: > 90%

### Phase 4 (Production)
- 🚀 Multi-instance: 3-node cluster tested
- ⭐ GitHub stars: 300+
- 👥 Community plugins: 5+
- 🏢 Enterprise users: 5+
- 📊 Uptime: > 99.9% for reference deployments
- 🌍 International usage: 10+ countries

---

## Resource Requirements

### Development Team
- **Phase 1:** 1 developer full-time (4-6 weeks)
- **Phase 2:** 1-2 developers (6-8 weeks)
- **Phase 3:** 1-2 developers (8-10 weeks)
- **Phase 4:** 1 developer + community contributions

### Infrastructure
- **Phase 1:** GitHub, PyPI, ReadTheDocs (free tier)
- **Phase 2:** Add demo deployment (Heroku/Railway free tier)
- **Phase 3:** Add monitoring (free tier Sentry/DataDog)
- **Phase 4:** Production reference architecture (AWS/GCP)

### Budget (Rough Estimates)
- **Phase 1:** $0 (all free tier)
- **Phase 2:** $50/month (demo deployments)
- **Phase 3:** $200/month (monitoring + staging)
- **Phase 4:** $500/month (production reference + CDN)

---

## Decision Points & Review Gates

### After Phase 0 (2 weeks)
**Review Question:** Is the POC promising?
- ✅ YES → Proceed to Phase 1
- ❌ NO → Revisit architecture, extend spike

### After Phase 1 (6 weeks)
**Review Questions:**
1. Can users build apps quickly? (< 5 min)
2. Is the API intuitive? (survey results)
3. Are there early adopters? (3+ developers)

**Decision:**
- ✅ All YES → Proceed to Phase 2
- ⚠️ Some NO → Iterate on Phase 1 for 2 more weeks
- ❌ All NO → Pivot or pause project

### After Phase 2 (14 weeks total)
**Review Questions:**
1. Does @action add value? (user feedback)
2. Is admin UI useful? (usage metrics)
3. Is there community momentum? (50+ stars, 3+ examples)

**Decision:**
- ✅ All YES → Proceed to Phase 3
- ⚠️ Some NO → Polish Phase 2 for 4 more weeks
- ❌ All NO → Reconsider value proposition

### After Phase 3 (24 weeks total)
**Review Questions:**
1. Are enterprise patterns being used? (1+ production deployment)
2. Is performance acceptable? (< 10ms overhead)
3. Is documentation complete? (user survey)

**Decision:**
- ✅ All YES → Proceed to Phase 4
- ⚠️ Some NO → Stabilize Phase 3 for 6 more weeks
- ❌ All NO → Focus on polish over new features

---

## Deferred Features (Post-Phase 4)

These are intentionally out of scope for initial roadmap:

### Potential Future Work
- [ ] GraphQL adapter (auto-generate from entities)
- [ ] gRPC adapter (typed RPC from entities)
- [ ] Real-time collaboration (CRDT-based sync)
- [ ] Multi-tenant support
- [ ] Data warehouse integration
- [ ] Machine learning ops integration
- [ ] Mobile SDK (React Native/Flutter integration)
- [ ] Desktop app support (Electron/Tauri integration)

**Decision Rule:** Only add these if there's clear user demand (10+ requests) and they align with core mission.

---

## Key Dates (Tentative)

| Milestone | Target Date | Status |
|-----------|------------|--------|
| Phase 0 Complete | Feb 1, 2025 | 🟡 In Progress |
| Phase 1.1 (Persistence) | Feb 15, 2025 | ⚪ Not Started |
| Phase 1.2 (Entity) | Feb 28, 2025 | ⚪ Not Started |
| Phase 1.3 (Examples) | Mar 7, 2025 | ⚪ Not Started |
| Phase 1 Release | Mar 15, 2025 | ⚪ Not Started |
| Phase 2.1 (@action design) | Mar 22, 2025 | ⚪ Not Started |
| Phase 2.2 (Dispatcher) | Apr 5, 2025 | ⚪ Not Started |
| Phase 2.3 (@action impl) | Apr 19, 2025 | ⚪ Not Started |
| Phase 2.4 (Backends) | May 3, 2025 | ⚪ Not Started |
| Phase 2.5 (Admin UI) | May 17, 2025 | ⚪ Not Started |
| Phase 2 Release | May 31, 2025 | ⚪ Not Started |
| Phase 3.1 (CQRS) | Jun 14, 2025 | ⚪ Not Started |
| Phase 3.2 (UoW) | Jun 28, 2025 | ⚪ Not Started |
| Phase 3.3 (Event Bus) | Jul 12, 2025 | ⚪ Not Started |
| Phase 3 Release | Aug 15, 2025 | ⚪ Not Started |
| Phase 4 (Ongoing) | Sep 2025 - Jun 2026 | ⚪ Not Started |

---

## Communication Plan

### Internal (Team)
- **Daily:** Async updates in project chat
- **Weekly:** Sync meeting (30 min) to review progress
- **Per Milestone:** Retrospective to identify improvements

### External (Community)
- **Monthly:** Blog post with progress update
- **Per Phase:** Release announcement (blog + social media)
- **Quarterly:** Community survey for feedback
- **Ad-hoc:** Twitter/Discord for quick updates

---

## Final Thoughts

This roadmap is **ambitious but achievable**. Each phase delivers standalone value while building toward the vision. The key is:

1. **Ship early** - Phase 1 alone is useful
2. **Iterate based on feedback** - Decision points allow course correction
3. **Build community** - Growth compounds over time
4. **Maintain focus** - Defer aggressively, add only what users request

**The North Star:** A Python developer can build a production-ready web application with rich domain logic, hybrid persistence, and clean architecture in under 100 lines of code.

**Success looks like:** In 18 months, Nitro is the default choice for Python developers who value domain modeling and want Rails-like productivity without Rails-like constraints.

---

**Document Owner:** Nikola Dendic  
**Last Review:** January 2025  
**Next Review:** After Phase 0 completion  
**Status:** LIVING DOCUMENT - Updates based on progress and learnings
# Changelog

All notable changes to the Nitro Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- FastAPI integration with full CRUD support
- Memory and SQL persistence backends
- Migration guide from StarModel
- Comprehensive test suite (141/171 features)

## [1.0.0] - TBD (Phase 1 Release)

### Added - Core Features
- **Entity System**: Rich domain entities with Pydantic validation
  - `Entity` base class with SQLModel integration
  - Core methods: `save()`, `delete()`, `get()`, `exists()`, `all()`
  - Query methods: `where()`, `search()`, `filter()`, `find_by()`
  - Signal generation for reactive UIs

- **Hybrid Persistence**: Pluggable repository backends
  - `SQLModelRepository`: SQL database persistence with session management
  - `MemoryRepository`: In-memory storage with TTL support
  - Repository interface for custom backends
  - Singleton repository per entity type

- **Event System**: Async-compatible event bus
  - `@on()` decorator for event handlers
  - `emit()` and `emit_async()` for event emission
  - Support for sync/async handlers and generators
  - Wildcard and namespace event support

- **Reactive Templating**: Rust-powered HTML generation
  - RustyTags integration (3-10x faster than pure Python)
  - `Page` component with CDN management
  - Datastar SDK for reactive UIs
  - `Signals` system for reactive state

- **CLI Tools**: Developer productivity features
  - `nitro tw init/dev/build`: Tailwind CSS integration
  - `nitro db init/migrate`: Database management
  - Smart configuration with environment variables

### Framework Integrations
- ✅ FastAPI: Full CRUD with < 50 lines
- ✅ Starlette: Minimal reactive counter
- ✅ FastHTML: Todo app with Page() integration
- ✅ Flask: Multi-route todo application

### Documentation
- Getting started guide
- API reference
- Migration guide from StarModel
- Framework integration examples

### Performance
- HTML generation 3-10x faster via RustyTags
- < 10ms overhead per request for framework
- Singleton repositories for efficient resource usage

---

## Breaking Changes Policy

### Major Versions (x.0.0)
Breaking changes are **only** introduced in major version updates. These are clearly marked with:

#### 🔴 BREAKING CHANGE
A clear description of what changed, why it changed, and how to migrate.

**Example:**
```
🔴 BREAKING CHANGE: Entity.save() return value
- Old: Returns None
- New: Returns bool (True on success)
- Migration: Update code checking save() return values
```

### Minor Versions (1.x.0)
- New features added
- No breaking changes to existing APIs
- Deprecation warnings for future removals

### Patch Versions (1.0.x)
- Bug fixes
- Performance improvements
- Documentation updates
- No API changes

---

## Deprecation Policy

When features are deprecated:

1. **Deprecation Warning**: Feature still works but emits `DeprecationWarning`
2. **Minimum Grace Period**: Feature remains for at least 1 major version
3. **Migration Guide**: Clear instructions provided in warning and changelog
4. **Removal**: Feature removed in next major version

### Deprecated Features

None yet - project is in Phase 1 (v1.0.0 preparation).

---

## Migration Guides

### From StarModel to Nitro

See [`examples/migration_from_starmodel.md`](examples/migration_from_starmodel.md) for detailed migration guide.

**Quick Summary:**
```python
# StarModel
from starmodel import *
class Counter(State):
    count: int = 0
    @event
    def increment(self):
        self.count += 1

# Nitro
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository

class Counter(Entity, table=True):
    count: int = 0
    model_config = {"repository_class": MemoryRepository}

    def increment(self):
        self.count += 1
        self.save()  # Explicit save
```

**Key Changes:**
- Import: `starmodel` → `nitro.domain.entities.base_entity`
- Class: `State` → `Entity`
- Config: Add `model_config` with repository selection
- Persistence: Add explicit `.save()` calls

---

## Version History

### [0.1.0] - Phase 0 (Proof of Concept)
- Initial entity and repository implementation
- FastAPI, Starlette, FastHTML, Flask examples
- Basic CLI tools
- Test coverage: 82.5% (141/171 features)

---

## Future Roadmap

### Phase 2: Auto-Magic (Q2 2025)
- Auto-routing with `@event` decorator
- CRUD UI generation
- Admin interface
- Additional framework adapters

### Phase 3: Enterprise (H2 2025)
- CQRS pattern implementation
- Unit of Work pattern
- Multi-instance coordination
- Background job processing

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style and testing requirements

## License

[License information]

## Credits

Nitro Framework evolved from StarModel's proven entity-centric patterns.
Built with love using Rust (RustyTags) and Python (FastAPI, Pydantic, SQLModel).

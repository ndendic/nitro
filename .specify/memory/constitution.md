<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0
- Modified principles: Event-Driven Architecture → Optional Module Architecture (clarifies modules are optional)
- Added sections: Planned Features and Modules (roadmap and module requirements)
- Templates requiring updates: ⚠ plan-template.md needs constitution check update
- No deferred TODOs
-->

# Nitro Constitution

## Core Principles

### I. Framework Agnostic
Nitro MUST be compatible with all major Python web frameworks including FastAPI, FastHTML, Django, Flask, and Sanic. No feature shall depend on a specific framework. All integrations MUST be implemented through adapter patterns that preserve the core functionality across frameworks. This ensures maximum adoption and prevents vendor lock-in for developers.

### II. Rust Core Performance
All HTML generation and templating core operations MUST use the Rust-based rusty-tags backend for optimal performance. Python-layer features MUST NOT bypass the Rust core for performance-critical paths. This principle ensures the 3-10x performance advantage over pure Python solutions is maintained as the framework evolves.

### III. Developer Experience First
Every API design decision MUST prioritize developer joy and productivity over internal implementation convenience. Features MUST include comprehensive examples, clear error messages, and intuitive APIs that feel natural to Python developers. Complex operations MUST be exposed through simple, readable interfaces.

### IV. Modularity
All functionality MUST be implemented as independent, composable modules that can be used selectively. Modules MUST have clear, minimal dependencies and well-defined interfaces. This enables developers to adopt only the features they need without bloat, similar to Laravel's modular architecture.

### V. Optional Module Architecture
Nitro MUST provide powerful optional modules that developers can choose to adopt based on their needs. No module shall be mandatory for basic functionality. Each module MUST be independently usable and well-documented. This principle enables developers to start simple and progressively enhance their applications with advanced features as needed.

## Planned Features and Modules

Nitro's roadmap includes these optional modules that developers can adopt as needed:

### Core Enhancement Modules
- **Event-Driven CQRS**: Optional Blinker-based event system for Command Query Responsibility Segregation patterns, enabling audit logging, state synchronization, and loose coupling
- **Datastar Integration**: Enhanced reactive component support with improved client-server communication
- **Template Scaffolding**: Pre-built templates and scaffolding tools for rapid development

### Developer Experience Modules
- **Tailwind Integration**: Standalone CDN/CLI support for rapid styling with utility-first CSS
- **Active Record Pattern**: Database interaction layer with intuitive ORM-like patterns for Python web development
- **Auto Layout System**: Automatic layout generation for database models and forms

### Advanced Features (Future)
- **Component Library**: Pre-built UI components following modern design patterns

Each module MUST:
- Function independently without requiring other optional modules
- Include comprehensive documentation and examples
- Maintain framework agnosticism across all supported Python web frameworks
- Follow the same performance and developer experience standards as the core

## Performance Standards

Nitro MUST maintain superior performance characteristics:
- HTML generation MUST be 3-10x faster than pure Python solutions
- Memory usage MUST be optimized through intelligent pooling and caching
- Component rendering MUST achieve sub-microsecond performance for simple elements
- All performance optimizations MUST be benchmarked and regression-tested

## Integration Requirements

Framework integration adapters MUST:
- Preserve all Nitro features across different frameworks
- Use framework-native response types when available
- Maintain consistent API surface regardless of underlying framework
- Include comprehensive integration tests for each supported framework

## Development Workflow

All features MUST follow TDD (Test-Driven Development):
- Tests written and approved before implementation begins
- Contract tests MUST be created for all public APIs
- Integration tests MUST cover framework compatibility
- Performance benchmarks MUST be included for core functionality

Code review MUST verify:
- Framework agnosticism is maintained
- Performance characteristics are preserved
- Developer experience is optimal
- Event-driven patterns are properly implemented

## Governance

This constitution supersedes all other development practices and guidelines. All pull requests and code reviews MUST verify compliance with these principles.

Amendments require:
- Documentation of the proposed change and rationale
- Approval from core maintainers
- Migration plan for existing features
- Update of dependent documentation and templates

Complexity deviations MUST be justified with:
- Clear explanation of why simpler alternatives are insufficient
- Performance or compatibility requirements that necessitate the complexity
- Plan for future simplification when constraints are removed

**Version**: 1.1.0 | **Ratified**: 2025-09-26 | **Last Amended**: 2025-09-26
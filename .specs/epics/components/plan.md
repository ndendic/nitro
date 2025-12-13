# Basecoat UI Components Implementation Plan

## Overview

Implement 29 remaining Basecoat UI components in the Nitro framework, replacing Basecoat's vanilla JavaScript with Datastar SDK reactivity. Components will use a mixed styling approach (data attributes for theming, cva() for complex layout) with separate CSS files per component.

## Desired End State

All 37 Basecoat components implemented with:
1. Consistent API following nitro-components skill guidelines
2. Datastar SDK replacing all vanilla JavaScript
3. **Basecoat CSS classes** - components output existing Basecoat class names
4. Users can override/extend styling via `cls` parameter (Tailwind classes)
5. Full accessibility (ARIA attributes, keyboard navigation)
6. **No new CSS files** - use and extend existing `docs_app/static/css/basecoat/components/`

### Verification:
- Each component renders correctly in docs_app with Basecoat styling
- Components output correct Basecoat classes (e.g., `btn-sm-outline`, `badge-secondary`)
- All ARIA attributes present and valid
- Keyboard navigation works (Tab, Enter, Escape, Arrow keys)
- Dark mode theming works via Basecoat CSS variables
- TypeScript/Pyright type hints pass

## What We're NOT Doing

- Server-side form validation (use client-side Datastar)
- Complex animations beyond CSS transitions
- Legacy browser support (using modern CSS like `anchor()`, `:has()`)
- JavaScript-only positioning (CSS anchor positioning where available)
- Custom icon system (using existing LucideIcon wrapper)

## Performance Considerations

- No JavaScript bundles - Datastar is CDN-loaded
- CSS is modular - only import what you use
- Components are pure functions - no class instantiation overhead
- Signals are reactive but minimal - no virtual DOM

## References

- Research: `docs/research/2025-12-12-basecoat-component-implementation.md`
- Skill: `.claude/skills/nitro-components/SKILL.md`
- Existing components: `nitro/nitro/infrastructure/html/components/`
- **Basecoat CSS (local)**: `nitro/docs_app/static/css/basecoat/components/`
- **Basecoat CSS (form)**: `nitro/docs_app/static/css/basecoat/components/form/`
- Basecoat website: https://basecoatui.com/
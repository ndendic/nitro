---
title: Test Page
category: Getting Started
order: 1
---

# Test Header

This is a test page with various markdown elements.

## Second Level Header

Here's some **bold text** and *italic text*.

### Code Example

```python
def hello():
    print("Hello, World!")
```

### List Example

- Item 1
- Item 2
- Item 3

### Nested List Example

- Parent Item 1
  - Child Item 1.1
  - Child Item 1.2
- Parent Item 2
  - Child Item 2.1
    - Grandchild Item 2.1.1
    - Grandchild Item 2.1.2
  - Child Item 2.2
- Parent Item 3

## Third Section

This is `inline code` in a paragraph.

> This is a blockquote with some important information.

### Link Examples

Here are different types of links:

1. [Internal link](/documentation/test-page) - should use Datastar navigation
2. [External link](https://example.com) - should open in new tab
3. [Anchor link](#test-header) - should jump to the header
4. [Another external](https://github.com) - another external link test

### Image Examples

![Alt text for image](https://via.placeholder.com/400x200 "This is the image title")

Regular image without title:
![Just alt text](https://via.placeholder.com/300x150)

### Table Example

| Name | Age | City |
|------|-----|------|
| Alice | 30 | NYC |
| Bob | 25 | LA |
| Charlie | 35 | Chicago |

Table with alignment:

| Left | Center | Right |
|:-----|:------:|------:|
| A | B | C |
| D | E | F |

### Alert Examples

::: info
This is an informational alert with some **important** information. It can contain markdown content.
:::

::: warning
This is a warning alert. Be careful with this operation!
:::

::: danger
This is a danger alert. This action cannot be undone!
:::

::: tip
This is a helpful tip. Try using keyboard shortcuts for faster navigation.
:::

### Interactive Component Demos

These demos showcase interactive Nitro components:

#### Button Demo

::demo:button

#### Dialog Demo

::demo:dialog

#### CodeBlock Demo

::demo:codeblock

#### Unknown Component Test

::demo:nonexistent

"""Debug test for markdown rendering"""

import sys
sys.path.insert(0, '/home/ndendic/Projects/auto-nitro/nitro/docs_app')

from infrastructure.markdown.renderer import NitroRenderer
import mistletoe

markdown = """```python
print('hello')
```"""

print("Parsing markdown...")
doc = mistletoe.Document(markdown)
print(f"Document: {doc}")
print(f"Document children: {doc.children}")

for child in doc.children:
    print(f"  Child: {child}")
    print(f"  Child type: {type(child).__name__}")
    if hasattr(child, 'children'):
        print(f"  Child's children: {child.children}")
    if hasattr(child, 'language'):
        print(f"  Language: {child.language}")

print("\nRendering...")
with NitroRenderer() as renderer:
    result = renderer.render(doc)

print(f"Result: {result}")
print(f"Result type: {type(result)}")

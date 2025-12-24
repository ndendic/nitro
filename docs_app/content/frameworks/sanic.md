# Sanic Integration

> **Status: Experimental**
>
> Sanic integration is in experimental stages. The adapter code exists but is not yet production-ready or part of the official Nitro package.

## Experimental Status

There is experimental Sanic integration code in the repository's `xPlay/datastart_nitro/` directory. This code demonstrates the feasibility of Nitro + Sanic integration but has not been:

- Fully tested in production environments
- Integrated into the main Nitro package
- Documented with comprehensive examples
- Validated for performance and reliability

**Use at your own risk in production applications.**

## Why Sanic?

Sanic is an async Python web framework designed for speed. It's a good fit for Nitro because:

- **Native async support** - Built on asyncio from the ground up
- **High performance** - Comparable to Node.js and Go frameworks
- **Modern syntax** - Python 3.7+ async/await patterns
- **WebSocket support** - Great for real-time applications

## Experimental Code Location

Experimental Sanic integration can be found in:

```
xPlay/datastart_nitro/
```

This directory contains proof-of-concept code demonstrating:

- SanicDispatcher implementation
- Route registration from @action decorators
- Parameter extraction from Sanic requests
- SSE integration with Sanic

**Note:** This code is experimental and may change significantly before becoming part of the official Nitro package.

## Datastar + Sanic

The `datastar_py` library includes official Sanic support for SSE integration:

```python
from sanic import Sanic
from datastar_py.sanic import datastar_response

app = Sanic("MyApp")

@app.route("/events")
async def sse_endpoint(request):
    """Stream updates using Datastar."""
    async def event_stream():
        # Your SSE logic here
        yield "data: message\n\n"

    return datastar_response(event_stream())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

See the [datastar_py documentation](https://github.com/starfederation/datastar-py) for Sanic-specific SSE helpers.

## Using Nitro Entities with Sanic (Manual Integration)

While auto-routing is experimental, you can use Nitro entities manually in Sanic applications:

```python
from sanic import Sanic, response
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository

app = Sanic("NitroSanicApp")

# Define entity
class Product(Entity, table=True):
    name: str
    price: float
    stock: int = 0

# Initialize database
SQLModelRepository().init_db()

# Manual route definitions (no auto-routing)
@app.route("/products", methods=["GET"])
async def list_products(request):
    """List all products."""
    products = Product.all()
    return response.json([p.model_dump() for p in products])

@app.route("/products/<product_id>/restock", methods=["POST"])
async def restock_product(request, product_id):
    """Restock a product."""
    product = Product.get(product_id)
    if not product:
        return response.json({"error": "Not found"}, status=404)

    quantity = request.json.get("quantity", 0)
    product.stock += quantity
    product.save()

    return response.json(product.model_dump())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

## What Needs to be Done?

To bring Sanic support to production-ready status:

1. **Complete SanicDispatcher** - Finish implementation and testing
2. **Integration Tests** - Comprehensive test suite
3. **Performance Benchmarks** - Validate performance claims
4. **Documentation** - Complete integration guide
5. **Examples** - Real-world example applications
6. **Error Handling** - Consistent error responses
7. **Package Integration** - Include in main Nitro package

## Contributing

If you'd like to help stabilize Sanic support, contributions are welcome!

Here's how to get started:

1. **Review experimental code** in `xPlay/datastart_nitro/`
2. **Test with real applications** and report issues
3. **Submit PRs** with improvements and bug fixes
4. **Write tests** for the SanicDispatcher
5. **Create examples** demonstrating integration

See the contribution guidelines in the [Nitro repository](https://github.com/your-repo/nitro).

## Why Still Experimental?

Several factors keep Sanic integration experimental:

1. **Limited Testing** - Needs more real-world usage
2. **API Stability** - Sanic's API occasionally changes
3. **Community Adoption** - Smaller community than FastAPI/Flask
4. **Maintenance Burden** - Need dedicated maintainer

We want to ensure any official adapter is production-ready and well-maintained.

## Timeline

Sanic integration may be promoted to stable status in a future release, depending on:

- Community interest and contributions
- Production usage reports
- Dedicated maintainer availability

Check the [project roadmap](https://github.com/your-repo/nitro/blob/main/docs/roadmap.md) for updates.

## Alternative: Use FastAPI for Async

If you need production-ready async support now, consider using **FastAPI** instead:

```python
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()
configure_nitro(app)  # Full auto-routing support

# FastAPI provides:
# ✅ Native async support
# ✅ Auto-generated OpenAPI docs
# ✅ Production-ready Nitro integration
# ✅ Large community and ecosystem
```

See [FastAPI Integration](./fastapi.md) for details.

## Next Steps

- **[Framework Overview](./overview.md)** - Framework-agnostic design
- **[FastAPI Integration](./fastapi.md)** - Production-ready async framework
- **[Starlette Integration](./starlette.md)** - SSE helpers (Sanic-compatible)

## Get Notified

Want updates on Sanic support? Star and watch the [Nitro repository](https://github.com/your-repo/nitro) on GitHub.

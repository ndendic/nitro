"""Framework adapter middleware for GraphQL endpoints.

Provides request handlers that integrate the ``GraphQLExecutor`` with
Sanic (primary) or any WSGI/ASGI framework via a generic interface.

Supports:
- GET  /graphql?query=...&variables=...
- POST /graphql  with JSON body ``{query, variables, operationName}``
- GET  /graphql?       (no query param)  → GraphiQL IDE HTML page

Public API
----------
graphql_handler(executor) -> callable
    Returns an async Sanic request handler.

register_graphql_route(app, executor, path="/graphql", graphiql=True)
    Convenience function to register the handler on a Sanic app.

graphiql_html(endpoint) -> str
    Return the GraphiQL IDE HTML page as a string.
"""
from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .executor import GraphQLExecutor


# ---------------------------------------------------------------------------
# GraphiQL HTML template
# ---------------------------------------------------------------------------

GRAPHIQL_VERSION = "3.0.9"


def graphiql_html(endpoint: str = "/graphql") -> str:
    """Return a self-contained GraphiQL IDE HTML page.

    Args:
        endpoint: The GraphQL endpoint URL (used by GraphiQL for requests).

    Returns:
        HTML string.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Nitro GraphiQL</title>
  <style>
    body {{ height: 100%; margin: 0; overflow: hidden; }}
    #graphiql {{ height: 100vh; }}
  </style>
  <script
    crossorigin
    src="https://unpkg.com/react@18/umd/react.production.min.js"
  ></script>
  <script
    crossorigin
    src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"
  ></script>
  <link rel="stylesheet" href="https://unpkg.com/graphiql@{GRAPHIQL_VERSION}/graphiql.min.css" />
</head>
<body>
  <div id="graphiql">Loading&hellip;</div>
  <script
    src="https://unpkg.com/graphiql@{GRAPHIQL_VERSION}/graphiql.min.js"
    type="application/javascript"
  ></script>
  <script>
    const fetcher = GraphiQL.createFetcher({{ url: '{endpoint}' }});
    ReactDOM.render(
      React.createElement(GraphiQL, {{ fetcher: fetcher }}),
      document.getElementById('graphiql'),
    );
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Generic request/response helpers
# ---------------------------------------------------------------------------

def _parse_request_body(body: bytes, content_type: str = "") -> dict[str, Any]:
    """Parse a request body into a GraphQL request dict."""
    if not body:
        return {}
    try:
        return json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _build_graphql_response(result_dict: dict[str, Any], status: int = 200) -> tuple[str, int]:
    """Serialize the execution result to JSON and HTTP status."""
    return json.dumps(result_dict), status


# ---------------------------------------------------------------------------
# Sanic handler
# ---------------------------------------------------------------------------

def graphql_handler(executor: "GraphQLExecutor"):
    """Return an async Sanic request handler for the given executor.

    The handler:
    - Serves GraphiQL IDE for GET requests with no ``query`` parameter.
    - Handles GET requests with ``?query=...`` query parameter.
    - Handles POST requests with JSON body.

    Args:
        executor: Configured ``GraphQLExecutor`` instance.

    Returns:
        Async Sanic handler function.
    """
    from .executor import ExecutionResult

    async def _handler(request):
        try:
            from sanic.response import HTTPResponse
        except ImportError as exc:
            raise ImportError(
                "Sanic is required for graphql_handler. Install with: pip install sanic"
            ) from exc

        method = request.method.upper()

        if method == "GET":
            query_param = request.args.get("query")
            if not query_param:
                # Serve GraphiQL
                html = graphiql_html(request.path)
                return HTTPResponse(body=html, status=200, content_type="text/html; charset=utf-8")

            variables_raw = request.args.get("variables", "{}")
            try:
                variables = json.loads(variables_raw) if variables_raw else {}
            except (json.JSONDecodeError, ValueError):
                variables = {}
            operation_name = request.args.get("operationName")
            result = executor.execute(query_param, variables, operation_name)
            body, status = _build_graphql_response(result.to_dict())
            return HTTPResponse(body=body, status=status, content_type="application/json")

        if method == "POST":
            content_type = request.content_type or ""
            body_bytes = request.body or b""
            gql_request = _parse_request_body(body_bytes, content_type)

            query = gql_request.get("query", "")
            variables = gql_request.get("variables") or {}
            operation_name = gql_request.get("operationName")

            if not query:
                body, status = _build_graphql_response(
                    {"errors": [{"message": "Missing 'query' in request body"}]},
                    status=400,
                )
                return HTTPResponse(body=body, status=status, content_type="application/json")

            result = executor.execute(query, variables, operation_name)
            body, status = _build_graphql_response(result.to_dict())
            return HTTPResponse(body=body, status=status, content_type="application/json")

        # Method not allowed
        return HTTPResponse(
            body=json.dumps({"errors": [{"message": "Method not allowed"}]}),
            status=405,
            content_type="application/json",
        )

    _handler.__name__ = "graphql_handler"
    return _handler


def register_graphql_route(
    app: Any,
    executor: "GraphQLExecutor",
    path: str = "/graphql",
    graphiql: bool = True,
) -> None:
    """Register a GraphQL route on a Sanic application.

    Registers both GET and POST methods on *path*.

    Args:
        app: Sanic application instance.
        executor: Configured ``GraphQLExecutor`` instance.
        path: URL path for the GraphQL endpoint (default: ``/graphql``).
        graphiql: If True, serve GraphiQL IDE on GET with no query param (default: True).

    Example::

        from sanic import Sanic
        from nitro.graphql import GraphQLExecutor, register_graphql_route
        from nitro.graphql.schema import generate_schema
        from nitro.graphql.resolvers import build_resolvers

        app = Sanic("MyApp")
        schema = generate_schema([Product, Order])
        resolvers = build_resolvers([Product, Order])
        executor = GraphQLExecutor(schema, resolvers)
        register_graphql_route(app, executor)
    """
    try:
        import sanic  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Sanic is required for register_graphql_route. Install with: pip install sanic"
        ) from exc

    handler = graphql_handler(executor)

    app.add_route(handler, path, methods=["GET", "POST"], name="graphql_endpoint")

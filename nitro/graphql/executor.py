"""Lightweight GraphQL query executor.

This module provides a minimal, zero-dependency GraphQL parser and executor.
It handles:
- Document parsing (queries, mutations, fragments)
- Variable substitution
- Resolver dispatch
- Introspection queries (``__schema``, ``__type``, ``__typename``)
- Optional ``graphql-core`` integration (used automatically when available)

Public API
----------
GraphQLExecutor(schema_sdl, resolvers)
    The main executor class.

ExecutionResult(data, errors)
    Holds the result of a query execution.

parse_query(query_str) -> Document
    Parse a GraphQL query string into an AST.

execute(query, variables, operation_name) -> ExecutionResult
    Parse and execute a query against the resolver map.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Try graphql-core first
# ---------------------------------------------------------------------------

try:
    from graphql import (
        build_schema as _gql_build_schema,
        graphql_sync as _gql_execute_sync,
        parse as _gql_parse,
    )
    _GRAPHQL_CORE_AVAILABLE = True
except ImportError:
    _GRAPHQL_CORE_AVAILABLE = False


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    """Result of a GraphQL query execution."""
    data: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.data is not None:
            result["data"] = self.data
        if self.errors:
            result["errors"] = self.errors
        return result


# ---------------------------------------------------------------------------
# Minimal AST / parser
# ---------------------------------------------------------------------------

class _Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind: str, value: str) -> None:
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.kind!r}, {self.value!r})"


def _tokenize(text: str) -> list[_Token]:
    """Produce a flat list of tokens from a GraphQL document."""
    tokens: list[_Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Skip whitespace and commas
        if ch in " \t\r\n,":
            i += 1
            continue
        # Skip line comments
        if ch == "#":
            while i < n and text[i] != "\n":
                i += 1
            continue
        # Block strings (""" ... """)
        if text[i : i + 3] == '"""':
            i += 3
            start = i
            while i < n - 2 and text[i : i + 3] != '"""':
                i += 1
            tokens.append(_Token("STRING", text[start:i]))
            i += 3
            continue
        # Regular strings
        if ch == '"':
            i += 1
            start = i
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            tokens.append(_Token("STRING", text[start:i]))
            i += 1
            continue
        # Punctuation
        if ch in "{}()[]!:=|&@":
            tokens.append(_Token("PUNCT", ch))
            i += 1
            continue
        # Spread "..."
        if text[i : i + 3] == "...":
            tokens.append(_Token("SPREAD", "..."))
            i += 3
            continue
        # Names and numbers
        if ch.isalpha() or ch == "_" or ch == "$":
            start = i
            while i < n and (text[i].isalnum() or text[i] in "_"):
                i += 1
            tokens.append(_Token("NAME", text[start:i]))
            continue
        if ch.isdigit() or (ch == "-" and i + 1 < n and text[i + 1].isdigit()):
            start = i
            if ch == "-":
                i += 1
            while i < n and (text[i].isdigit() or text[i] in ".eE+-"):
                i += 1
            tokens.append(_Token("NUMBER", text[start:i]))
            continue
        # Unknown — skip
        i += 1

    return tokens


@dataclass
class _Field:
    name: str
    alias: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    selection_set: List["_Field"] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)

    @property
    def response_key(self) -> str:
        return self.alias if self.alias else self.name


@dataclass
class _OperationDef:
    operation: str  # "query" | "mutation" | "subscription"
    name: Optional[str]
    variables: Dict[str, Any]
    selection_set: List[_Field]


@dataclass
class _FragmentDef:
    name: str
    type_condition: str
    selection_set: List[_Field]


@dataclass
class _Document:
    operations: List[_OperationDef] = field(default_factory=list)
    fragments: Dict[str, _FragmentDef] = field(default_factory=dict)


class _ParseError(Exception):
    pass


class _Parser:
    """Recursive-descent parser for a small GraphQL subset."""

    def __init__(self, tokens: list[_Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _peek(self) -> Optional[_Token]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect_punct(self, ch: str) -> None:
        tok = self._advance()
        if tok.kind != "PUNCT" or tok.value != ch:
            raise _ParseError(f"Expected '{ch}', got {tok!r}")

    def _expect_name(self) -> str:
        tok = self._advance()
        if tok.kind != "NAME":
            raise _ParseError(f"Expected NAME, got {tok!r}")
        return tok.value

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    def parse_document(self) -> _Document:
        doc = _Document()
        while self._peek() is not None:
            tok = self._peek()
            if tok.kind == "NAME" and tok.value in ("query", "mutation", "subscription"):
                doc.operations.append(self._parse_operation())
            elif tok.kind == "NAME" and tok.value == "fragment":
                frag = self._parse_fragment()
                doc.fragments[frag.name] = frag
            elif tok.kind == "PUNCT" and tok.value == "{":
                # Anonymous shorthand query
                sel = self._parse_selection_set()
                doc.operations.append(_OperationDef("query", None, {}, sel))
            else:
                # Skip unknown token
                self._advance()
        return doc

    def _parse_operation(self) -> _OperationDef:
        operation = self._advance().value  # query/mutation/subscription
        name: Optional[str] = None
        variables: dict[str, Any] = {}

        tok = self._peek()
        if tok and tok.kind == "NAME":
            name = self._advance().value

        # Variable definitions ( ... )
        tok = self._peek()
        if tok and tok.kind == "PUNCT" and tok.value == "(":
            variables = self._parse_variable_defs()

        sel = self._parse_selection_set()
        return _OperationDef(operation, name, variables, sel)

    def _parse_variable_defs(self) -> dict[str, Any]:
        """Parse variable definitions (types only — values come from input)."""
        self._expect_punct("(")
        defs: dict[str, Any] = {}
        while True:
            tok = self._peek()
            if tok and tok.kind == "PUNCT" and tok.value == ")":
                self._advance()
                break
            if tok and tok.kind == "PUNCT" and tok.value == "$":
                self._advance()
                var_name = self._expect_name()
                self._expect_punct(":")
                type_str = self._parse_type_string()
                defs[var_name] = type_str
                # Optional default value
                tok2 = self._peek()
                if tok2 and tok2.kind == "PUNCT" and tok2.value == "=":
                    self._advance()
                    self._parse_value()  # consume default
            else:
                break
        return defs

    def _parse_type_string(self) -> str:
        """Parse a GraphQL type reference (String, String!, [String!]!)."""
        tok = self._peek()
        if tok and tok.kind == "PUNCT" and tok.value == "[":
            self._advance()
            inner = self._parse_type_string()
            self._expect_punct("]")
            result = f"[{inner}]"
        else:
            result = self._expect_name()
        tok2 = self._peek()
        if tok2 and tok2.kind == "PUNCT" and tok2.value == "!":
            self._advance()
            result += "!"
        return result

    def _parse_fragment(self) -> _FragmentDef:
        self._advance()  # "fragment"
        name = self._expect_name()
        self._expect_name()  # "on"
        type_condition = self._expect_name()
        sel = self._parse_selection_set()
        return _FragmentDef(name, type_condition, sel)

    # ------------------------------------------------------------------
    # Selection set / fields
    # ------------------------------------------------------------------

    def _parse_selection_set(self) -> list[_Field]:
        self._expect_punct("{")
        fields: list[_Field] = []
        while True:
            tok = self._peek()
            if tok is None or (tok.kind == "PUNCT" and tok.value == "}"):
                break
            if tok.kind == "SPREAD":
                # Fragment spread — store as synthetic field __fragment__:<name>
                self._advance()
                tok2 = self._peek()
                if tok2 and tok2.kind == "NAME" and tok2.value == "on":
                    # Inline fragment — parse and flatten
                    self._advance()
                    self._expect_name()  # type condition
                    inner = self._parse_selection_set()
                    fields.extend(inner)
                elif tok2 and tok2.kind == "NAME":
                    frag_name = self._advance().value
                    fields.append(_Field(name=f"__fragment__:{frag_name}"))
                continue
            fields.append(self._parse_field())
        self._expect_punct("}")
        return fields

    def _parse_field(self) -> _Field:
        name = self._expect_name()
        alias: Optional[str] = None

        tok = self._peek()
        if tok and tok.kind == "PUNCT" and tok.value == ":":
            # alias: name
            self._advance()
            alias = name
            name = self._expect_name()

        arguments: dict[str, Any] = {}
        tok = self._peek()
        if tok and tok.kind == "PUNCT" and tok.value == "(":
            arguments = self._parse_arguments()

        # Directives
        directives: list[str] = []
        while True:
            tok = self._peek()
            if tok and tok.kind == "PUNCT" and tok.value == "@":
                self._advance()
                d_name = self._expect_name()
                directives.append(d_name)
                # Directive arguments
                tok2 = self._peek()
                if tok2 and tok2.kind == "PUNCT" and tok2.value == "(":
                    self._parse_arguments()
            else:
                break

        selection_set: list[_Field] = []
        tok = self._peek()
        if tok and tok.kind == "PUNCT" and tok.value == "{":
            selection_set = self._parse_selection_set()

        return _Field(
            name=name,
            alias=alias,
            arguments=arguments,
            selection_set=selection_set,
            directives=directives,
        )

    def _parse_arguments(self) -> dict[str, Any]:
        self._expect_punct("(")
        args: dict[str, Any] = {}
        while True:
            tok = self._peek()
            if tok is None or (tok.kind == "PUNCT" and tok.value == ")"):
                self._advance()
                break
            name = self._expect_name()
            self._expect_punct(":")
            value = self._parse_value()
            args[name] = value
        return args

    def _parse_value(self) -> Any:
        tok = self._peek()
        if tok is None:
            raise _ParseError("Unexpected end of input in value")

        if tok.kind == "PUNCT" and tok.value == "$":
            # Variable reference
            self._advance()
            name = self._expect_name()
            return {"__var__": name}

        if tok.kind == "NUMBER":
            self._advance()
            v = tok.value
            return float(v) if "." in v or "e" in v.lower() else int(v)

        if tok.kind == "STRING":
            self._advance()
            return tok.value

        if tok.kind == "NAME":
            self._advance()
            if tok.value == "true":
                return True
            if tok.value == "false":
                return False
            if tok.value == "null":
                return None
            return tok.value  # enum value

        if tok.kind == "PUNCT" and tok.value == "[":
            self._advance()
            items = []
            while True:
                t = self._peek()
                if t and t.kind == "PUNCT" and t.value == "]":
                    self._advance()
                    break
                items.append(self._parse_value())
            return items

        if tok.kind == "PUNCT" and tok.value == "{":
            self._advance()
            obj: dict[str, Any] = {}
            while True:
                t = self._peek()
                if t and t.kind == "PUNCT" and t.value == "}":
                    self._advance()
                    break
                k = self._expect_name()
                self._expect_punct(":")
                v = self._parse_value()
                obj[k] = v
            return obj

        # Unrecognized — skip
        self._advance()
        return None


def parse_query(query_str: str) -> _Document:
    """Parse a GraphQL query string into an AST ``_Document``."""
    tokens = _tokenize(query_str)
    return _Parser(tokens).parse_document()


# ---------------------------------------------------------------------------
# Introspection
# ---------------------------------------------------------------------------

_INTROSPECTION_TYPES = {
    "String": {"kind": "SCALAR", "name": "String", "description": "Built-in String scalar"},
    "Int": {"kind": "SCALAR", "name": "Int", "description": "Built-in Int scalar"},
    "Float": {"kind": "SCALAR", "name": "Float", "description": "Built-in Float scalar"},
    "Boolean": {"kind": "SCALAR", "name": "Boolean", "description": "Built-in Boolean scalar"},
    "ID": {"kind": "SCALAR", "name": "ID", "description": "Built-in ID scalar"},
    "JSON": {"kind": "SCALAR", "name": "JSON", "description": "Arbitrary JSON scalar"},
}


def _build_introspection_schema(schema_sdl: str) -> dict[str, Any]:
    """Build a minimal introspection schema dict from SDL."""
    type_defs: dict[str, Any] = dict(_INTROSPECTION_TYPES)

    # Parse type names from SDL with a simple regex
    for match in re.finditer(r"\btype\s+(\w+)\s*\{", schema_sdl):
        name = match.group(1)
        type_defs[name] = {"kind": "OBJECT", "name": name, "fields": []}

    for match in re.finditer(r"\binput\s+(\w+)\s*\{", schema_sdl):
        name = match.group(1)
        type_defs[name] = {"kind": "INPUT_OBJECT", "name": name, "inputFields": []}

    for match in re.finditer(r"\bscalar\s+(\w+)", schema_sdl):
        name = match.group(1)
        type_defs[name] = {"kind": "SCALAR", "name": name}

    return {
        "__schema": {
            "queryType": {"name": "Query"},
            "mutationType": {"name": "Mutation"} if "type Mutation" in schema_sdl else None,
            "subscriptionType": None,
            "types": list(type_defs.values()),
            "directives": [],
        }
    }


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class GraphQLExecutor:
    """Execute GraphQL queries against a resolver map.

    Supports:
    - Query and Mutation operations
    - Variable substitution
    - Nested field selection
    - Introspection (``__schema``, ``__type``, ``__typename``)
    - Optional ``graphql-core`` backend (auto-detected)

    Args:
        schema_sdl: SDL string describing the schema (from ``generate_schema()``).
        resolvers: Resolver map (from ``build_resolvers()``).

    Example::

        executor = GraphQLExecutor(schema_sdl, resolvers)
        result = executor.execute("{ products { id name } }")
        print(result.data)
    """

    def __init__(self, schema_sdl: str, resolvers: dict[str, Any]) -> None:
        self._schema_sdl = schema_sdl
        self._resolvers = resolvers
        self._introspection = _build_introspection_schema(schema_sdl)
        self._use_graphql_core = _GRAPHQL_CORE_AVAILABLE

        if self._use_graphql_core:
            try:
                self._gql_schema = _gql_build_schema(schema_sdl)
            except Exception:
                self._use_graphql_core = False

    # ------------------------------------------------------------------
    # Public execute
    # ------------------------------------------------------------------

    def execute(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> "ExecutionResult":
        """Execute a GraphQL query string.

        Args:
            query: GraphQL query/mutation document string.
            variables: Variable values dict (optional).
            operation_name: Name of operation to execute when doc has multiple (optional).

        Returns:
            ``ExecutionResult`` with ``data`` and ``errors`` fields.
        """
        variables = variables or {}

        if self._use_graphql_core:
            return self._execute_with_graphql_core(query, variables, operation_name)
        return self._execute_builtin(query, variables, operation_name)

    # ------------------------------------------------------------------
    # graphql-core backend
    # ------------------------------------------------------------------

    def _execute_with_graphql_core(
        self,
        query: str,
        variables: dict[str, Any],
        operation_name: Optional[str],
    ) -> "ExecutionResult":
        from graphql import build_schema, graphql_sync
        from graphql.type import GraphQLResolveInfo

        # Build resolver callables wrapped for graphql-core signature
        root_value: dict[str, Any] = {}
        for type_name, fields in self._resolvers.items():
            for field_name, fn in fields.items():
                # graphql-core calls resolver(root, info, **args)
                root_value[field_name] = fn

        try:
            gql_result = graphql_sync(
                self._gql_schema,
                query,
                root_value=root_value,
                variable_values=variables,
                operation_name=operation_name,
            )
            errors = []
            if gql_result.errors:
                errors = [{"message": str(e)} for e in gql_result.errors]
            return ExecutionResult(data=gql_result.data, errors=errors)
        except Exception as exc:
            return ExecutionResult(errors=[{"message": str(exc)}])

    # ------------------------------------------------------------------
    # Built-in executor
    # ------------------------------------------------------------------

    def _execute_builtin(
        self,
        query: str,
        variables: dict[str, Any],
        operation_name: Optional[str],
    ) -> "ExecutionResult":
        try:
            doc = parse_query(query)
        except _ParseError as exc:
            return ExecutionResult(errors=[{"message": f"Syntax error: {exc}"}])

        if not doc.operations:
            return ExecutionResult(errors=[{"message": "No operations found in query"}])

        # Select the operation
        op: Optional[_OperationDef] = None
        if operation_name:
            for candidate in doc.operations:
                if candidate.name == operation_name:
                    op = candidate
                    break
            if op is None:
                return ExecutionResult(errors=[{"message": f"Unknown operation: {operation_name}"}])
        else:
            op = doc.operations[0]

        try:
            data = self._execute_operation(op, variables, doc.fragments)
        except Exception as exc:
            return ExecutionResult(errors=[{"message": str(exc)}])

        return ExecutionResult(data=data)

    def _execute_operation(
        self,
        op: _OperationDef,
        variables: dict[str, Any],
        fragments: dict[str, _FragmentDef],
    ) -> dict[str, Any]:
        root_type = op.operation.capitalize()  # "Query" or "Mutation"
        type_resolvers = self._resolvers.get(root_type, {})

        data: dict[str, Any] = {}
        for sel_field in op.selection_set:
            key, value = self._resolve_field(
                sel_field, root_type, type_resolvers, None, variables, fragments
            )
            data[key] = value
        return data

    def _resolve_args(
        self,
        raw_args: dict[str, Any],
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """Substitute variable references in arguments."""
        resolved: dict[str, Any] = {}
        for k, v in raw_args.items():
            resolved[k] = self._substitute_vars(v, variables)
        return resolved

    def _substitute_vars(self, value: Any, variables: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            if "__var__" in value:
                var_name = value["__var__"]
                return variables.get(var_name)
            return {k: self._substitute_vars(v, variables) for k, v in value.items()}
        if isinstance(value, list):
            return [self._substitute_vars(item, variables) for item in value]
        return value

    def _resolve_field(
        self,
        sel_field: _Field,
        parent_type: str,
        type_resolvers: dict[str, Any],
        parent_value: Any,
        variables: dict[str, Any],
        fragments: dict[str, _FragmentDef],
    ) -> tuple[str, Any]:
        name = sel_field.name
        response_key = sel_field.response_key

        # Meta-fields
        if name == "__typename":
            return response_key, parent_type

        if name == "__schema":
            return response_key, self._introspection.get("__schema")

        if name == "__type":
            args = self._resolve_args(sel_field.arguments, variables)
            type_name = args.get("name", "")
            schema = self._introspection.get("__schema", {})
            types = {t["name"]: t for t in schema.get("types", [])}
            return response_key, types.get(type_name)

        # Regular field from resolver
        resolver = type_resolvers.get(name)
        if resolver is None:
            # Try parent value dict
            if isinstance(parent_value, dict):
                return response_key, parent_value.get(name)
            if hasattr(parent_value, name):
                return response_key, getattr(parent_value, name)
            return response_key, None

        args = self._resolve_args(sel_field.arguments, variables)
        raw_value = resolver(parent_value, None, **args)

        # If sub-selection, recurse
        if sel_field.selection_set and raw_value is not None:
            value = self._apply_selection(
                raw_value, parent_type, sel_field.selection_set, variables, fragments
            )
        else:
            value = raw_value

        return response_key, value

    def _apply_selection(
        self,
        raw_value: Any,
        parent_type: str,
        selection_set: list[_Field],
        variables: dict[str, Any],
        fragments: dict[str, _FragmentDef],
    ) -> Any:
        """Apply a selection set to a resolved value (dict or list of dicts)."""
        if isinstance(raw_value, list):
            return [
                self._apply_selection(item, parent_type, selection_set, variables, fragments)
                for item in raw_value
            ]

        if not isinstance(raw_value, dict):
            # Coerce to dict if possible
            if hasattr(raw_value, "model_dump"):
                raw_value = raw_value.model_dump()
            elif hasattr(raw_value, "__dict__"):
                raw_value = {k: v for k, v in vars(raw_value).items() if not k.startswith("_")}
            else:
                return raw_value

        result: dict[str, Any] = {}
        for sel_field in selection_set:
            if sel_field.name.startswith("__fragment__:"):
                frag_name = sel_field.name.split(":", 1)[1]
                frag = fragments.get(frag_name)
                if frag:
                    for frag_field in frag.selection_set:
                        fkey = frag_field.response_key
                        result[fkey] = raw_value.get(fkey)
                continue

            if sel_field.name == "__typename":
                result[sel_field.response_key] = parent_type
                continue

            field_value = raw_value.get(sel_field.name)
            if sel_field.selection_set and field_value is not None:
                field_value = self._apply_selection(
                    field_value, sel_field.name, sel_field.selection_set, variables, fragments
                )
            result[sel_field.response_key] = field_value

        return result

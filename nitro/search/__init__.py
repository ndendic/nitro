"""
nitro.search — Full-text search for Nitro entities and arbitrary content.

Provides:
- SearchIndex     : Abstract base class for search backends
- MemorySearchIndex : In-memory search with TF-IDF ranking (no deps)
- SQLiteSearchIndex : SQLite FTS5-backed search (production-ready)
- searchable      : Decorator to auto-index entity fields on save
- SearchResult    : Pydantic model for a single search hit

Quick start::

    from nitro.search import MemorySearchIndex, SearchResult

    index = MemorySearchIndex()

    # Index documents
    index.index("doc:1", {"title": "Python Web Framework", "body": "Nitro is fast"})
    index.index("doc:2", {"title": "Rust Performance", "body": "RustyTags generates HTML"})

    # Search
    results = index.search("fast framework")
    # [SearchResult(doc_id="doc:1", score=..., highlights={"title": "Python Web <mark>Framework</mark>"})]

    # Remove from index
    index.remove("doc:1")

    # Rebuild index
    index.rebuild()

SQLite FTS5 backend (production)::

    from nitro.search import SQLiteSearchIndex

    index = SQLiteSearchIndex(db_path="search.db")
    index.index("product:1", {"name": "Nitro Widget", "description": "A fast widget"})
    results = index.search("fast widget")

Entity integration::

    from nitro.search import MemorySearchIndex, searchable

    index = MemorySearchIndex()

    @searchable(index, fields=["name", "description"])
    class Product(Entity, table=True):
        name: str = ""
        description: str = ""

    # Products are auto-indexed on save
    p = Product(id="p1", name="Widget", description="A useful widget")
    p.save()

    results = index.search("useful")
    # [SearchResult(doc_id="Product:p1", score=...)]
"""

from __future__ import annotations

import math
import re
import sqlite3
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    """A single search hit."""
    doc_id: str
    score: float
    highlights: Dict[str, str] = field(default_factory=dict)
    snippet: str = ""

    def __repr__(self) -> str:
        return f"SearchResult(doc_id={self.doc_id!r}, score={self.score:.4f})"


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class SearchIndex(ABC):
    """Abstract base class for search backends."""

    @abstractmethod
    def index(self, doc_id: str, fields: Dict[str, str]) -> None:
        """Add or update a document in the index."""

    @abstractmethod
    def remove(self, doc_id: str) -> bool:
        """Remove a document from the index. Returns True if found."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Search the index. Returns ranked results."""

    @abstractmethod
    def count(self) -> int:
        """Return number of indexed documents."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all documents from the index."""

    def rebuild(self) -> None:
        """Rebuild internal data structures. Override if needed."""


# ---------------------------------------------------------------------------
# Tokenizer utilities
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")

# Common English stop words
_STOP_WORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "from", "has", "have", "he", "in", "is", "it", "its", "of", "on",
    "or", "she", "that", "the", "to", "was", "were", "will", "with",
}


def tokenize(text: str, remove_stops: bool = True) -> List[str]:
    """Tokenize text into lowercase words, optionally removing stop words."""
    tokens = _WORD_RE.findall(text.lower())
    if remove_stops:
        tokens = [t for t in tokens if t not in _STOP_WORDS]
    return tokens


def highlight_text(text: str, terms: Set[str], tag: str = "mark") -> str:
    """Wrap matching terms in highlight tags."""
    def _replace(match: re.Match) -> str:
        word = match.group(0)
        if word.lower() in terms:
            return f"<{tag}>{word}</{tag}>"
        return word
    return _WORD_RE.sub(_replace, text)


# ---------------------------------------------------------------------------
# MemorySearchIndex — TF-IDF based, no external dependencies
# ---------------------------------------------------------------------------

class MemorySearchIndex(SearchIndex):
    """In-memory full-text search using TF-IDF ranking.

    Good for development, testing, and small datasets (< 100k documents).
    For larger datasets, use SQLiteSearchIndex.
    """

    def __init__(self) -> None:
        # doc_id -> {field_name: original_text}
        self._docs: Dict[str, Dict[str, str]] = {}
        # doc_id -> {field_name: [tokens]}
        self._doc_tokens: Dict[str, Dict[str, List[str]]] = {}
        # term -> set of doc_ids containing it
        self._inverted: Dict[str, Set[str]] = defaultdict(set)
        # Total token count per document (for TF normalization)
        self._doc_lengths: Dict[str, int] = {}

    def index(self, doc_id: str, fields: Dict[str, str]) -> None:
        # Remove old entry if exists
        if doc_id in self._docs:
            self._remove_from_inverted(doc_id)

        self._docs[doc_id] = dict(fields)
        doc_tokens: Dict[str, List[str]] = {}
        total_len = 0

        for fname, text in fields.items():
            tokens = tokenize(str(text))
            doc_tokens[fname] = tokens
            total_len += len(tokens)
            for token in set(tokens):
                self._inverted[token].add(doc_id)

        self._doc_tokens[doc_id] = doc_tokens
        self._doc_lengths[doc_id] = max(total_len, 1)

    def remove(self, doc_id: str) -> bool:
        if doc_id not in self._docs:
            return False
        self._remove_from_inverted(doc_id)
        del self._docs[doc_id]
        del self._doc_tokens[doc_id]
        del self._doc_lengths[doc_id]
        return True

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        n_docs = len(self._docs)
        if n_docs == 0:
            return []

        # Score each candidate document using TF-IDF
        scores: Dict[str, float] = defaultdict(float)
        query_terms = set(query_tokens)

        for term in query_tokens:
            if term not in self._inverted:
                continue
            doc_ids = self._inverted[term]
            idf = math.log(1 + n_docs / len(doc_ids))

            for doc_id in doc_ids:
                doc_tok = self._doc_tokens[doc_id]
                tf = 0
                for fname, tokens in doc_tok.items():
                    if fields and fname not in fields:
                        continue
                    tf += tokens.count(term)
                if tf == 0:
                    continue  # Term not in requested fields
                # Normalize TF by document length
                tf_norm = tf / self._doc_lengths[doc_id]
                scores[doc_id] += tf_norm * idf

        if not scores:
            return []

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        page = ranked[offset:offset + limit]

        results = []
        for doc_id, score in page:
            doc_fields = self._docs[doc_id]
            highlights = {}
            for fname, text in doc_fields.items():
                if fields and fname not in fields:
                    continue
                highlighted = highlight_text(text, query_terms)
                if highlighted != text:
                    highlights[fname] = highlighted

            # Build snippet from first highlighted field
            snippet = ""
            if highlights:
                first_field = next(iter(highlights.values()))
                snippet = first_field[:200]

            results.append(SearchResult(
                doc_id=doc_id,
                score=score,
                highlights=highlights,
                snippet=snippet,
            ))

        return results

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()
        self._doc_tokens.clear()
        self._inverted.clear()
        self._doc_lengths.clear()

    def rebuild(self) -> None:
        docs = dict(self._docs)
        self.clear()
        for doc_id, fields in docs.items():
            self.index(doc_id, fields)

    def _remove_from_inverted(self, doc_id: str) -> None:
        if doc_id not in self._doc_tokens:
            return
        for tokens in self._doc_tokens[doc_id].values():
            for token in set(tokens):
                self._inverted[token].discard(doc_id)
                if not self._inverted[token]:
                    del self._inverted[token]


# ---------------------------------------------------------------------------
# SQLiteSearchIndex — FTS5-backed, production-ready
# ---------------------------------------------------------------------------

class SQLiteSearchIndex(SearchIndex):
    """SQLite FTS5-backed full-text search.

    Production-ready for datasets up to millions of documents.
    Uses SQLite's built-in FTS5 extension for efficient indexing and ranking.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        table_name: str = "search_index",
    ) -> None:
        self._db_path = db_path
        self._table = table_name
        self._fields_table = f"{table_name}_fields"
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._known_fields: Set[str] = set()
        self._setup_tables()

    def _setup_tables(self) -> None:
        """Create the FTS5 virtual table and metadata table."""
        # Metadata table to track doc_id -> field mappings
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._fields_table} (
                doc_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                field_value TEXT NOT NULL,
                PRIMARY KEY (doc_id, field_name)
            )
        """)
        # FTS5 table for full-text search
        self._conn.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self._table}
            USING fts5(doc_id, content, tokenize='porter unicode61')
        """)
        self._conn.commit()

    def index(self, doc_id: str, fields: Dict[str, str]) -> None:
        # Remove old entry
        self.remove(doc_id)

        # Concatenate all field values for FTS indexing
        content = " ".join(str(v) for v in fields.values())

        self._conn.execute(
            f"INSERT INTO {self._table}(doc_id, content) VALUES (?, ?)",
            (doc_id, content),
        )

        # Store individual fields for highlighting
        for fname, fval in fields.items():
            self._conn.execute(
                f"INSERT OR REPLACE INTO {self._fields_table}(doc_id, field_name, field_value) "
                "VALUES (?, ?, ?)",
                (doc_id, fname, str(fval)),
            )
            self._known_fields.add(fname)

        self._conn.commit()

    def remove(self, doc_id: str) -> bool:
        cur = self._conn.execute(
            f"SELECT rowid FROM {self._table} WHERE doc_id = ?", (doc_id,)
        )
        rows = cur.fetchall()
        if not rows:
            return False

        for (rowid,) in rows:
            self._conn.execute(
                f"DELETE FROM {self._table} WHERE rowid = ?", (rowid,)
            )
        self._conn.execute(
            f"DELETE FROM {self._fields_table} WHERE doc_id = ?", (doc_id,)
        )
        self._conn.commit()
        return True

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        tokens = tokenize(query, remove_stops=False)
        if not tokens:
            return []

        # Build FTS5 query — OR between terms for broader matching
        fts_query = " OR ".join(tokens)

        try:
            cur = self._conn.execute(
                f"SELECT doc_id, rank FROM {self._table} "
                f"WHERE {self._table} MATCH ? "
                "ORDER BY rank "
                "LIMIT ? OFFSET ?",
                (fts_query, limit, offset),
            )
        except sqlite3.OperationalError:
            return []

        rows = cur.fetchall()
        if not rows:
            return []

        query_terms = set(tokenize(query))
        results = []

        for doc_id, rank in rows:
            # Fetch field values for highlighting
            fcur = self._conn.execute(
                f"SELECT field_name, field_value FROM {self._fields_table} WHERE doc_id = ?",
                (doc_id,),
            )
            doc_fields = dict(fcur.fetchall())

            highlights = {}
            for fname, text in doc_fields.items():
                if fields and fname not in fields:
                    continue
                highlighted = highlight_text(text, query_terms)
                if highlighted != text:
                    highlights[fname] = highlighted

            snippet = ""
            if highlights:
                first_field = next(iter(highlights.values()))
                snippet = first_field[:200]

            # FTS5 rank is negative (lower = better), convert to positive score
            results.append(SearchResult(
                doc_id=doc_id,
                score=abs(rank),
                highlights=highlights,
                snippet=snippet,
            ))

        return results

    def count(self) -> int:
        cur = self._conn.execute(f"SELECT COUNT(DISTINCT doc_id) FROM {self._table}")
        return cur.fetchone()[0]

    def clear(self) -> None:
        self._conn.execute(f"DELETE FROM {self._table}")
        self._conn.execute(f"DELETE FROM {self._fields_table}")
        self._conn.commit()

    def rebuild(self) -> None:
        self._conn.execute(f"INSERT INTO {self._table}({self._table}) VALUES('rebuild')")
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __del__(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# @searchable decorator — auto-index entities on save
# ---------------------------------------------------------------------------

def searchable(
    index: SearchIndex,
    fields: List[str],
    doc_id_prefix: Optional[str] = None,
) -> Callable:
    """Decorator to auto-index entity fields when save() is called.

    Args:
        index: The SearchIndex instance to use.
        fields: List of entity field names to index.
        doc_id_prefix: Optional prefix for doc IDs (default: class name).

    Usage::

        index = MemorySearchIndex()

        @searchable(index, fields=["name", "description"])
        class Product(Entity, table=True):
            name: str = ""
            description: str = ""
    """
    def decorator(cls: Type) -> Type:
        prefix = doc_id_prefix or cls.__name__
        original_save = cls.save

        def _index_entity(entity: Any) -> None:
            doc_id = f"{prefix}:{entity.id}"
            field_data = {}
            for fname in fields:
                val = getattr(entity, fname, "")
                if val is not None:
                    field_data[fname] = str(val)
            if field_data:
                index.index(doc_id, field_data)

        def patched_save(self, *args, **kwargs):
            result = original_save(self, *args, **kwargs)
            _index_entity(self)
            return result

        cls.save = patched_save

        # Also patch delete to remove from index
        original_delete = cls.delete

        def patched_delete(self, *args, **kwargs):
            doc_id = f"{prefix}:{self.id}"
            index.remove(doc_id)
            return original_delete(self, *args, **kwargs)

        cls.delete = patched_delete

        # Store metadata on class for introspection
        cls._search_index = index
        cls._search_fields = fields
        cls._search_prefix = prefix

        return cls

    return decorator


__all__ = [
    "SearchIndex",
    "MemorySearchIndex",
    "SQLiteSearchIndex",
    "SearchResult",
    "searchable",
    "tokenize",
    "highlight_text",
]

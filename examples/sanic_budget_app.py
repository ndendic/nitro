"""
Sanic Budget Tracker — Computed Aggregations with Visual Data

Demonstrates:
  1. Computed aggregations — totals by category, overall spending, budget %
  2. Visual data representation — progress bars for budget utilization
  3. Category-based organization — expenses grouped by category with icons
  4. Summary statistics — derived metrics from entity data (not raw metrics)
  5. Inline category management — add/remove budget categories
  6. publish_sync + SSE.patch_elements for multi-region updates

Run:
    cd nitro && python examples/sanic_budget_app.py
    Then visit http://localhost:8010
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///budget.db")

import uuid
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import Div, H1, H2, H3, P, Span, Button, Input, Select, Option

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

CATEGORIES = {
    "food": ("Food & Dining", "bg-orange-500", "bg-orange-50 text-orange-700 border-orange-200"),
    "transport": ("Transport", "bg-blue-500", "bg-blue-50 text-blue-700 border-blue-200"),
    "utilities": ("Utilities", "bg-violet-500", "bg-violet-50 text-violet-700 border-violet-200"),
    "entertainment": ("Entertainment", "bg-pink-500", "bg-pink-50 text-pink-700 border-pink-200"),
    "health": ("Health", "bg-emerald-500", "bg-emerald-50 text-emerald-700 border-emerald-200"),
    "shopping": ("Shopping", "bg-amber-500", "bg-amber-50 text-amber-700 border-amber-200"),
    "other": ("Other", "bg-gray-500", "bg-gray-50 text-gray-700 border-gray-200"),
}

CATEGORY_BUDGETS = {
    "food": 500,
    "transport": 200,
    "utilities": 150,
    "entertainment": 100,
    "health": 200,
    "shopping": 300,
    "other": 150,
}


class Expense(Entity, table=True):
    """A single expense entry."""
    __tablename__ = "budget_expense"
    description: str = ""
    amount: float = 0.0
    category: str = "other"
    date: str = ""

    @classmethod
    @post()
    def add(cls, description: str = "", amount: str = "0", category: str = "other", request=None):
        """Add a new expense."""
        description = description.strip()
        try:
            amt = round(float(amount), 2)
        except (ValueError, TypeError):
            amt = 0
        if not description or amt <= 0:
            return {"error": "invalid"}
        expense = cls(
            id=uuid.uuid4().hex[:8],
            description=description,
            amount=amt,
            category=category,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        expense.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"description": "", "amount": ""}))
        return {"id": expense.id}

    @post()
    def remove(self, request=None):
        """Delete this expense."""
        self.delete()
        _broadcast_all()
        return {"deleted": True}

    @classmethod
    @post()
    def clear_all(cls, request=None):
        """Clear all expenses."""
        for e in cls.all():
            e.delete()
        _broadcast_all()
        return {"cleared": True}


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _totals_by_category() -> dict[str, float]:
    """Sum expenses per category."""
    totals: dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
    for e in Expense.all():
        totals[e.category] = totals.get(e.category, 0.0) + e.amount
    return totals


def _grand_total() -> float:
    return sum(e.amount for e in Expense.all())


def _total_budget() -> float:
    return sum(CATEGORY_BUDGETS.values())


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------

def _broadcast_all():
    """Push all regions to connected SSE clients."""
    publish_sync("sse", SSE.patch_elements(summary_cards(), selector="#summary-cards"))
    publish_sync("sse", SSE.patch_elements(budget_bars(), selector="#budget-bars"))
    publish_sync("sse", SSE.patch_elements(expense_list(), selector="#expense-list"))


# ---------------------------------------------------------------------------
# Components — pure functions returning HTML
# ---------------------------------------------------------------------------

def summary_cards():
    """Top-level summary statistics derived from expense data."""
    total_spent = _grand_total()
    total_budget = _total_budget()
    expense_count = len(Expense.all())
    utilization = int((total_spent / total_budget * 100) if total_budget else 0)

    # Find highest spending category
    totals = _totals_by_category()
    top_cat = max(totals, key=totals.get) if any(totals.values()) else None
    top_cat_label = CATEGORIES[top_cat][0] if top_cat and totals[top_cat] > 0 else "—"

    return Div(
        # Total spent
        Div(
            Span("Total Spent", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(
                f"${total_spent:,.2f}",
                class_="text-3xl font-bold tabular-nums text-gray-900 mt-1",
            ),
            Span(
                f"of ${total_budget:,.2f} budget",
                class_="text-xs text-gray-400 mt-0.5",
            ),
            class_="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col",
        ),
        # Budget utilization
        Div(
            Span("Utilization", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(
                f"{utilization}%",
                class_=(
                    f"text-3xl font-bold tabular-nums mt-1 "
                    f"{'text-emerald-600' if utilization < 75 else 'text-amber-600' if utilization < 100 else 'text-red-600'}"
                ),
            ),
            # Mini progress bar
            Div(
                Div(
                    class_=(
                        f"h-full rounded-full transition-all "
                        f"{'bg-emerald-500' if utilization < 75 else 'bg-amber-500' if utilization < 100 else 'bg-red-500'}"
                    ),
                    style=f"width: {min(utilization, 100)}%",
                ),
                class_="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-2",
            ),
            class_="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col",
        ),
        # Expense count
        Div(
            Span("Expenses", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(
                str(expense_count),
                class_="text-3xl font-bold tabular-nums text-gray-900 mt-1",
            ),
            Span("entries this period", class_="text-xs text-gray-400 mt-0.5"),
            class_="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col",
        ),
        # Top category
        Div(
            Span("Top Category", class_="text-xs font-medium text-gray-500 uppercase tracking-wider"),
            Span(
                top_cat_label,
                class_="text-xl font-bold text-gray-900 mt-1",
            ),
            Span(
                f"${totals.get(top_cat, 0):,.2f}" if top_cat and totals[top_cat] > 0 else "No expenses",
                class_="text-xs text-gray-400 mt-0.5",
            ),
            class_="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex flex-col",
        ),
        id="summary-cards",
        class_="grid grid-cols-2 md:grid-cols-4 gap-4",
    )


def budget_bar(cat_key: str, spent: float):
    """A single category budget bar."""
    label, bar_color, badge_cls = CATEGORIES[cat_key]
    budget = CATEGORY_BUDGETS[cat_key]
    pct = int((spent / budget * 100) if budget else 0)
    over = spent > budget

    return Div(
        # Category label + amounts
        Div(
            Div(
                Span(label, class_=f"text-sm font-semibold {badge_cls} px-2.5 py-0.5 rounded-full border"),
                class_="flex items-center gap-2",
            ),
            Span(
                f"${spent:,.2f} / ${budget:,.0f}",
                class_=f"text-sm tabular-nums font-medium {'text-red-600' if over else 'text-gray-600'}",
            ),
            class_="flex items-center justify-between mb-1.5",
        ),
        # Progress bar
        Div(
            Div(
                class_=(
                    f"h-full rounded-full transition-all {bar_color} "
                    f"{'opacity-100' if not over else 'bg-red-500'}"
                ),
                style=f"width: {min(pct, 100)}%",
            ),
            class_="w-full h-3 bg-gray-100 rounded-full overflow-hidden",
        ),
        # Percentage label
        Div(
            Span(
                f"{pct}% used" if not over else f"{pct}% — over budget!",
                class_=f"text-xs {'text-gray-400' if not over else 'text-red-500 font-semibold'}",
            ),
            class_="mt-1 text-right",
        ),
        class_="py-3",
    )


def budget_bars():
    """Category budget bars — replaced by SSE."""
    totals = _totals_by_category()

    # Sort: highest spending first
    sorted_cats = sorted(CATEGORIES.keys(), key=lambda c: totals.get(c, 0), reverse=True)

    return Div(
        *[budget_bar(cat, totals.get(cat, 0)) for cat in sorted_cats],
        id="budget-bars",
        class_="divide-y divide-gray-100",
    )


def expense_row(expense: Expense):
    """A single expense row."""
    _, _, badge_cls = CATEGORIES.get(expense.category, CATEGORIES["other"])
    cat_label = CATEGORIES.get(expense.category, CATEGORIES["other"])[0]

    return Div(
        # Category badge
        Span(
            cat_label,
            class_=f"text-xs px-2 py-0.5 rounded-full font-medium {badge_cls} border shrink-0",
        ),
        # Description
        P(expense.description, class_="text-sm text-gray-800 flex-1 min-w-0 truncate"),
        # Amount
        Span(
            f"${expense.amount:,.2f}",
            class_="text-sm font-semibold tabular-nums text-gray-700 shrink-0",
        ),
        # Date
        Span(expense.date, class_="text-xs text-gray-400 shrink-0 hidden sm:inline"),
        # Delete
        Button(
            "\u00d7",
            title="Delete expense",
            class_=(
                "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                "hover:bg-red-50 transition-all text-sm flex items-center "
                "justify-center opacity-0 group-hover:opacity-100 shrink-0"
            ),
            on_click=action(expense.remove),
        ),
        class_=(
            "group flex items-center gap-3 px-4 py-3 "
            "border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors"
        ),
    )


def expense_list():
    """Expense list — replaced by SSE."""
    expenses = Expense.all()
    # Sort by date descending, then by id descending for same-day ordering
    expenses.sort(key=lambda e: (e.date, e.id), reverse=True)

    if not expenses:
        return Div(
            P(
                "No expenses yet. Add one above!",
                class_="text-gray-400 text-center text-sm italic py-8",
            ),
            id="expense-list",
        )

    return Div(
        *[expense_row(e) for e in expenses],
        id="expense-list",
        class_="bg-white rounded-xl border border-gray-200 overflow-hidden",
    )


def budget_page():
    """Full page layout — summary + budget bars + expense list."""
    return Page(
        Div(
            # Header
            Div(
                H1("Nitro Budget", class_="text-3xl font-bold text-gray-900"),
                P(
                    "Expense tracking with computed aggregations and budget visualization",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Summary cards
            summary_cards(),

            # Two-column layout: budget bars + add form / expense list
            Div(
                # Left: Budget breakdown
                Div(
                    Div(
                        H2(
                            "Budget Breakdown",
                            class_="text-xs font-bold uppercase tracking-wider text-gray-400",
                        ),
                        class_="mb-2",
                    ),
                    budget_bars(),
                    class_=(
                        "w-80 shrink-0 bg-white rounded-2xl "
                        "border border-gray-200 p-5 shadow-sm"
                    ),
                ),

                # Right: Add form + expense list
                Div(
                    # Add expense form
                    Div(
                        H3(
                            "Add Expense",
                            class_="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3",
                        ),
                        Div(
                            Input(
                                type="text",
                                placeholder="Description...",
                                bind="description",
                                class_=(
                                    "flex-1 px-4 py-2.5 rounded-lg border border-gray-200 "
                                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                                    "focus:ring-2 focus:ring-blue-100 outline-none "
                                    "transition-all text-sm text-gray-700 placeholder-gray-400"
                                ),
                            ),
                            Input(
                                type="number",
                                placeholder="0.00",
                                bind="amount",
                                step="0.01",
                                min="0",
                                class_=(
                                    "w-28 px-4 py-2.5 rounded-lg border border-gray-200 "
                                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                                    "focus:ring-2 focus:ring-blue-100 outline-none "
                                    "transition-all text-sm text-gray-700 placeholder-gray-400 "
                                    "tabular-nums"
                                ),
                            ),
                            Select(
                                *[
                                    Option(CATEGORIES[cat][0], value=cat)
                                    for cat in CATEGORIES
                                ],
                                bind="category",
                                class_=(
                                    "px-3 py-2.5 rounded-lg border border-gray-200 "
                                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                                    "focus:ring-2 focus:ring-blue-100 outline-none "
                                    "transition-all text-sm text-gray-700"
                                ),
                            ),
                            Button(
                                "Add",
                                class_=(
                                    "px-5 py-2.5 rounded-lg text-sm font-semibold text-white "
                                    "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                                    "transition-all shadow-sm"
                                ),
                                on_click=action(Expense.add),
                            ),
                            class_="flex gap-2 flex-wrap",
                            data_signals="{description: '', amount: '', category: 'food'}",
                        ),
                        class_="mb-6",
                    ),

                    # Expense list header with clear button
                    Div(
                        H2(
                            "Recent Expenses",
                            class_="text-xs font-bold uppercase tracking-wider text-gray-400",
                        ),
                        Button(
                            "Clear All",
                            class_=(
                                "px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-500 "
                                "bg-gray-100 hover:bg-gray-200 active:scale-95 "
                                "transition-all"
                            ),
                            on_click=action(Expense.clear_all),
                        ),
                        class_="flex items-center justify-between mb-3",
                    ),

                    # Expense list (replaced by SSE)
                    expense_list(),

                    class_="flex-1 min-w-0",
                ),

                class_="flex gap-6 items-start mt-8",
            ),

            # Footer
            Div(
                P(
                    "Open in multiple tabs — budgets and expenses sync in real time",
                    class_="text-xs text-gray-400 mt-8 text-center",
                ),
            ),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-5xl mx-auto px-6 py-12",
        ),
        title="Nitro Budget",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroBudget")
configure_nitro(app)


@app.before_server_start
async def setup(app):
    Expense.repository().init_db()


@app.get("/")
async def homepage(request: Request):
    return html(str(budget_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8010, debug=True, auto_reload=True)

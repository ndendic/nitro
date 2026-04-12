"""
Sanic Gallery — Image Gallery / Portfolio with Filtering & Lightbox

Demonstrates:
  1. Grid layout with card-based image display
  2. Category-based filtering + text search combo (server-side, same pattern as contacts)
  3. Lightbox detail view — click image card to see full details via SSE patch
  4. URL-based image upload simulation — paste URL + metadata form
  5. Category management — add/remove user-defined categories
  6. publish_sync + SSE.patch_elements for multi-region real-time updates

New patterns vs. prior examples:
  - Grid layout (3-column) replacing list/column layouts
  - Overlay/lightbox modal driven by signal + SSE content injection
  - Combined search + category filter (two orthogonal axes)
  - Visual card with image preview and category badge

Run:
    cd nitro && python examples/sanic_gallery_app.py
    Then visit http://localhost:8016
"""
import uuid
from datetime import datetime, timezone

from sanic import Sanic, Request
from sanic.response import html

from nitro import Entity, post, action, Client
from nitro.adapters.sanic_adapter import configure_nitro
from nitro.events import publish_sync
from nitro.html.datastar import SSE
from nitro.html import Page
from rusty_tags import (
    Div, H1, H2, H3, P, Span, Button, Input, Textarea, Select, Option,
    Label, Img, A,
)

from datastar_py.sanic import datastar_response


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

DEFAULT_CATEGORIES = [
    {"id": "nature", "name": "Nature", "color": "emerald"},
    {"id": "architecture", "name": "Architecture", "color": "blue"},
    {"id": "portrait", "name": "Portrait", "color": "violet"},
    {"id": "travel", "name": "Travel", "color": "amber"},
    {"id": "abstract", "name": "Abstract", "color": "rose"},
]

CATEGORY_COLORS = {
    "emerald": ("bg-emerald-100 text-emerald-700 border-emerald-200", "bg-emerald-500"),
    "blue":    ("bg-blue-100 text-blue-700 border-blue-200",          "bg-blue-500"),
    "violet":  ("bg-violet-100 text-violet-700 border-violet-200",    "bg-violet-500"),
    "amber":   ("bg-amber-100 text-amber-700 border-amber-200",       "bg-amber-500"),
    "rose":    ("bg-rose-100 text-rose-700 border-rose-200",          "bg-rose-500"),
    "slate":   ("bg-slate-100 text-slate-700 border-slate-200",       "bg-slate-500"),
    "cyan":    ("bg-cyan-100 text-cyan-700 border-cyan-200",          "bg-cyan-500"),
    "indigo":  ("bg-indigo-100 text-indigo-700 border-indigo-200",    "bg-indigo-500"),
}

SAMPLE_IMAGES = [
    {
        "title": "Mountain Sunrise",
        "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600",
        "description": "A breathtaking sunrise over snow-capped peaks casting golden light across the valley.",
        "category": "nature",
    },
    {
        "title": "Urban Geometry",
        "image_url": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=600",
        "description": "Bold lines and angles of modern architecture create an abstract pattern against the sky.",
        "category": "architecture",
    },
    {
        "title": "Street Portrait",
        "image_url": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=600",
        "description": "Candid portrait captured during golden hour, natural light softening the scene.",
        "category": "portrait",
    },
    {
        "title": "Santorini Cliffs",
        "image_url": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=600",
        "description": "Classic white-washed buildings cascading down volcanic cliffs over the Aegean Sea.",
        "category": "travel",
    },
    {
        "title": "Color Burst",
        "image_url": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=600",
        "description": "Vibrant ink diffusing through water creates an organic and unpredictable abstract form.",
        "category": "abstract",
    },
    {
        "title": "Forest Path",
        "image_url": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=600",
        "description": "A misty morning path winds through ancient trees, dappled light filtering through the canopy.",
        "category": "nature",
    },
]

# Server-side filter state
_current_search = ""
_current_category = ""


# ---------------------------------------------------------------------------
# Domain
# ---------------------------------------------------------------------------

class Category(Entity, table=True):
    """A gallery category tag."""
    __tablename__ = "gallery_category"
    name: str = ""
    color: str = "slate"

    @classmethod
    @post()
    def add_category(cls, cat_name: str = "", cat_color: str = "slate", request=None):
        """Create a new category."""
        cat_name = cat_name.strip()
        if not cat_name:
            return {"error": "empty"}
        cat = cls(id=uuid.uuid4().hex[:8], name=cat_name, color=cat_color)
        cat.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"cat_name": "", "cat_color": "slate"}))
        return {"id": cat.id}

    @post()
    def remove_category(self, request=None):
        """Delete this category."""
        # Move images in this category to uncategorized
        for img in GalleryImage.all():
            if img.category == self.id:
                img.category = ""
                img.save()
        self.delete()
        _broadcast_all()
        return {"deleted": True}


class GalleryImage(Entity, table=True):
    """An image in the gallery with metadata."""
    __tablename__ = "gallery_image"
    title: str = ""
    image_url: str = ""
    description: str = ""
    category: str = ""
    created_at: str = ""

    @classmethod
    @post()
    def add(cls, title: str = "", image_url: str = "", description: str = "",
            category: str = "", request=None):
        """Add a new image to the gallery."""
        title = title.strip()
        image_url = image_url.strip()
        if not title or not image_url:
            return {"error": "title and image_url required"}
        img = cls(
            id=uuid.uuid4().hex[:8],
            title=title,
            image_url=image_url,
            description=description.strip(),
            category=category,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
        img.save()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({
            "add_title": "", "add_url": "", "add_description": "",
            "add_category": "", "show_upload": False,
        }))
        return {"id": img.id}

    @post()
    def remove(self, request=None):
        """Delete this image."""
        self.delete()
        _broadcast_all()
        publish_sync("sse", SSE.patch_signals({"lightbox_id": ""}))
        return {"deleted": True}

    @classmethod
    @post()
    def search(cls, q: str = "", filter_category: str = "", request=None):
        """Server-side search + filter. Stores filter state, re-renders gallery."""
        global _current_search, _current_category
        _current_search = q.strip().lower()
        _current_category = filter_category
        _broadcast_all()
        return {"ok": True}


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def _get_filtered_images():
    """Return images matching current search text and category filter."""
    images = GalleryImage.all()
    if _current_search:
        q = _current_search
        images = [
            img for img in images
            if q in img.title.lower() or q in img.description.lower()
        ]
    if _current_category:
        images = [img for img in images if img.category == _current_category]
    images.sort(key=lambda img: img.created_at, reverse=True)
    return images


def _get_category_by_id(cat_id: str):
    """Look up a category by id, return None if not found."""
    return next((c for c in Category.all() if c.id == cat_id), None)


def _broadcast_all():
    """Push gallery grid + stats + filter bar to all clients."""
    publish_sync("sse", SSE.patch_elements(gallery_grid(), selector="#gallery-grid"))
    publish_sync("sse", SSE.patch_elements(gallery_stats(), selector="#gallery-stats"))
    publish_sync("sse", SSE.patch_elements(filter_bar(), selector="#filter-bar"))
    publish_sync("sse", SSE.patch_elements(category_manager(), selector="#category-manager"))


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def category_badge(cat_id: str, small: bool = False):
    """Small category pill for image cards."""
    cat = _get_category_by_id(cat_id)
    if not cat:
        return Span()
    badge_cls, _ = CATEGORY_COLORS.get(cat.color, CATEGORY_COLORS["slate"])
    size_cls = "text-[10px] px-1.5 py-0.5" if small else "text-xs px-2 py-1"
    return Span(
        cat.name,
        class_=f"font-semibold rounded-full border {badge_cls} {size_cls}",
    )


def image_card(img: GalleryImage):
    """A single gallery card — click to open lightbox."""
    return Div(
        # Image area — clicking opens lightbox
        Div(
            Img(
                src=img.image_url,
                alt=img.title,
                class_="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105",
                loading="lazy",
                onerror="this.src='https://placehold.co/600x400/e2e8f0/94a3b8?text=Image+not+found'",
            ),
            # Category badge overlay
            Div(
                category_badge(img.category, small=True),
                class_="absolute top-2 left-2",
            ),
            # Hover overlay with view hint
            Div(
                Span(
                    "View",
                    class_="text-white text-sm font-semibold",
                ),
                class_=(
                    "absolute inset-0 bg-black/0 group-hover:bg-black/30 "
                    "flex items-center justify-center transition-all duration-300"
                ),
            ),
            on_click=f"$lightbox_id = '{img.id}'; @get('/api/image/{img.id}')",
            class_="relative w-full h-48 overflow-hidden rounded-t-xl cursor-pointer bg-gray-100",
        ),
        # Card footer
        Div(
            Div(
                P(
                    img.title,
                    class_="text-sm font-semibold text-gray-800 truncate",
                ),
                P(
                    img.created_at,
                    class_="text-[10px] text-gray-400 mt-0.5",
                ),
            ),
            Button(
                "×",
                title="Delete image",
                class_=(
                    "w-6 h-6 rounded text-gray-300 hover:text-red-500 "
                    "hover:bg-red-50 transition-all text-sm flex items-center "
                    "justify-center opacity-0 group-hover:opacity-100"
                ),
                on_click=action(img.remove),
            ),
            class_="flex items-start justify-between",
        ),
        id=f"image-{img.id}",
        class_=(
            "group bg-white rounded-xl border border-gray-200 "
            "shadow-sm hover:shadow-md transition-all overflow-hidden"
        ),
    )


def gallery_grid():
    """The 3-column image grid — replaced by SSE on change."""
    images = _get_filtered_images()

    if not images:
        empty = Div(
            P(
                "No images found." if (_current_search or _current_category) else "No images yet.",
                class_="text-gray-400 text-center text-sm",
            ),
            P(
                "Try a different filter." if (_current_search or _current_category) else "Add your first image above.",
                class_="text-gray-300 text-center text-xs mt-1",
            ),
            class_="col-span-3 py-16",
        )
        return Div(
            empty,
            id="gallery-grid",
            class_="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4",
        )

    return Div(
        *[image_card(img) for img in images],
        id="gallery-grid",
        class_="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4",
    )


def gallery_stats():
    """Stats summary bar — replaced by SSE on change."""
    all_images = GalleryImage.all()
    filtered = _get_filtered_images()
    total = len(all_images)
    showing = len(filtered)

    if total == 0:
        return Div(id="gallery-stats")

    active_filter = _current_search or _current_category
    if active_filter and showing != total:
        text = f"Showing {showing} of {total} images"
    else:
        text = f"{total} image{'s' if total != 1 else ''} in gallery"

    return Div(
        Span(text, class_="text-sm text-gray-500"),
        id="gallery-stats",
        class_="text-center py-2",
    )


def filter_bar():
    """Category filter tabs — replaced by SSE on category change."""
    categories = Category.all()

    all_cls = (
        "px-4 py-2 rounded-full text-sm font-medium transition-all "
        + ("bg-gray-800 text-white" if not _current_category
           else "bg-gray-100 text-gray-600 hover:bg-gray-200")
    )

    tabs = [
        Button(
            "All",
            class_=all_cls,
            on_click=action(GalleryImage.search, q=_current_search, filter_category=""),
        )
    ]

    for cat in categories:
        badge_cls, dot_cls = CATEGORY_COLORS.get(cat.color, CATEGORY_COLORS["slate"])
        is_active = _current_category == cat.id
        tab_cls = (
            "px-4 py-2 rounded-full text-sm font-medium transition-all border "
            + (badge_cls + " ring-2 ring-offset-1 ring-current" if is_active
               else "bg-gray-100 text-gray-600 hover:bg-gray-200 border-transparent")
        )
        tabs.append(
            Button(
                cat.name,
                class_=tab_cls,
                on_click=action(GalleryImage.search, q=_current_search, filter_category=cat.id),
            )
        )

    return Div(
        *tabs,
        id="filter-bar",
        class_="flex items-center gap-2 flex-wrap",
    )


def category_manager():
    """Category management section — add/remove categories."""
    categories = Category.all()

    cat_chips = []
    for cat in categories:
        badge_cls, _ = CATEGORY_COLORS.get(cat.color, CATEGORY_COLORS["slate"])
        cat_chips.append(
            Div(
                Span(cat.name, class_=f"text-xs font-medium"),
                Button(
                    "×",
                    class_="ml-1 text-current opacity-60 hover:opacity-100 transition-all text-xs font-bold",
                    on_click=action(cat.remove_category),
                ),
                class_=f"flex items-center px-2 py-1 rounded-full border {badge_cls} text-xs",
            )
        )

    return Div(
        Div(
            Div(
                *cat_chips,
                class_="flex items-center gap-2 flex-wrap",
            ) if categories else Span(),
            Div(
                Input(
                    type="text",
                    placeholder="New category...",
                    bind="cat_name",
                    class_=(
                        "px-3 py-1.5 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "outline-none transition-all text-sm w-36"
                    ),
                ),
                Select(
                    *[Option(name.capitalize(), value=name) for name in CATEGORY_COLORS],
                    bind="cat_color",
                    class_="px-2 py-1.5 rounded-lg border border-gray-200 bg-gray-50 text-sm",
                ),
                Button(
                    "+",
                    class_=(
                        "px-3 py-1.5 rounded-lg bg-gray-800 text-white text-sm "
                        "font-medium hover:bg-gray-700 transition-all"
                    ),
                    on_click=action(Category.add_category),
                ),
                class_="flex items-center gap-2",
            ),
            class_="flex items-center gap-3 flex-wrap",
        ),
        id="category-manager",
    )


def lightbox_content(img: GalleryImage):
    """Full detail view for an image — injected via SSE into the lightbox."""
    return Div(
        # Close button
        Div(
            H3(img.title, class_="text-lg font-bold text-gray-900"),
            Button(
                "×",
                class_="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-xl transition-all",
                on_click="$lightbox_id = ''",
            ),
            class_="flex items-center justify-between mb-4",
        ),
        # Full image
        Div(
            Img(
                src=img.image_url,
                alt=img.title,
                class_="w-full h-auto rounded-xl object-cover max-h-96",
                onerror="this.src='https://placehold.co/800x500/e2e8f0/94a3b8?text=Image+not+found'",
            ),
            class_="mb-4 rounded-xl overflow-hidden bg-gray-100",
        ),
        # Metadata
        Div(
            Div(
                category_badge(img.category),
                Span(img.created_at, class_="text-xs text-gray-400 ml-2"),
                class_="flex items-center",
            ),
            class_="mb-3",
        ),
        # Description
        P(
            img.description or "No description.",
            class_="text-sm text-gray-600 leading-relaxed",
        ) if img.description else Span(),
        # URL
        Div(
            P("Image URL:", class_="text-xs font-medium text-gray-500 mb-1"),
            A(
                img.image_url,
                href=img.image_url,
                target="_blank",
                class_="text-xs text-blue-500 hover:underline break-all",
            ),
            class_="mt-4 pt-4 border-t border-gray-100",
        ),
        # Delete button
        Button(
            "Delete Image",
            class_=(
                "mt-4 w-full py-2 rounded-xl font-semibold text-white "
                "bg-red-500 hover:bg-red-600 active:scale-[0.98] transition-all"
            ),
            on_click=action(img.remove),
        ),
        id="lightbox-content",
    )


def lightbox():
    """The lightbox overlay — shown when lightbox_id signal is set."""
    return Div(
        # Backdrop
        Div(
            class_="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity",
            on_click="$lightbox_id = ''",
        ),
        # Panel
        Div(
            Div(
                P("Loading...", class_="text-gray-400 text-center py-8"),
                id="lightbox-content",
            ),
            class_=(
                "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 "
                "bg-white rounded-2xl shadow-2xl p-6 z-50 "
                "w-full max-w-lg max-h-[90vh] overflow-y-auto"
            ),
        ),
        id="lightbox",
        data_show="$lightbox_id !== ''",
        style="display:none",
    )


def upload_form():
    """Inline upload form — toggled by show_upload signal."""
    categories = Category.all()
    return Div(
        Div(
            H2("Add Image", class_="text-base font-bold text-gray-900"),
            Button(
                "×",
                class_="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-xl transition-all",
                on_click="$show_upload = false",
            ),
            class_="flex items-center justify-between mb-4",
        ),
        # Title + URL row
        Div(
            Div(
                Label("Title", class_="text-xs font-medium text-gray-600 mb-1 block"),
                Input(
                    type="text",
                    placeholder="Image title...",
                    bind="add_title",
                    class_=(
                        "w-full px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
                    ),
                ),
                class_="flex-1",
            ),
            Div(
                Label("Category", class_="text-xs font-medium text-gray-600 mb-1 block"),
                Select(
                    Option("Uncategorized", value=""),
                    *[Option(c.name, value=c.id) for c in categories],
                    bind="add_category",
                    class_=(
                        "w-full px-3 py-2 rounded-lg border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "outline-none transition-all text-sm"
                    ),
                ),
                class_="w-40",
            ),
            class_="flex gap-3 mb-3",
        ),
        # Image URL
        Div(
            Label("Image URL", class_="text-xs font-medium text-gray-600 mb-1 block"),
            Input(
                type="url",
                placeholder="https://example.com/image.jpg",
                bind="add_url",
                class_=(
                    "w-full px-3 py-2 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
                ),
            ),
            class_="mb-3",
        ),
        # Description
        Div(
            Label("Description", class_="text-xs font-medium text-gray-600 mb-1 block"),
            Textarea(
                bind="add_description",
                placeholder="Optional description...",
                rows="2",
                class_=(
                    "w-full px-3 py-2 rounded-lg border border-gray-200 "
                    "bg-gray-50 focus:bg-white focus:border-blue-400 "
                    "focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm resize-none"
                ),
            ),
            class_="mb-4",
        ),
        Button(
            "Add to Gallery",
            class_=(
                "w-full py-2.5 rounded-xl font-semibold text-white "
                "bg-blue-500 hover:bg-blue-600 active:scale-[0.98] "
                "transition-all shadow-sm"
            ),
            on_click=action(GalleryImage.add),
        ),
        class_=(
            "bg-white rounded-2xl border border-gray-200 shadow-md p-5 mb-6"
        ),
        data_show="$show_upload",
    )


def gallery_page():
    """Full page layout."""
    return Page(
        Div(
            # Header
            Div(
                H1(
                    "Nitro Gallery",
                    class_="text-3xl font-bold text-gray-900",
                ),
                P(
                    "Image portfolio with filtering, search, and lightbox preview",
                    class_="text-sm text-gray-500 mt-1",
                ),
                class_="text-center mb-8",
            ),

            # Top controls: search + upload button
            Div(
                Input(
                    type="text",
                    placeholder="Search images...",
                    bind="q",
                    on_input=action(GalleryImage.search),
                    class_=(
                        "flex-1 px-4 py-2.5 rounded-xl border border-gray-200 "
                        "bg-gray-50 focus:bg-white focus:border-blue-400 "
                        "focus:ring-2 focus:ring-blue-100 outline-none "
                        "transition-all text-gray-700 placeholder-gray-400 text-sm"
                    ),
                ),
                Button(
                    "+ Add Image",
                    class_=(
                        "px-5 py-2.5 rounded-xl font-semibold text-white "
                        "bg-blue-500 hover:bg-blue-600 active:scale-95 "
                        "transition-all shadow-sm text-sm"
                    ),
                    on_click="$show_upload = !$show_upload",
                ),
                class_="flex gap-3 mb-4",
                data_signals=(
                    "{q: '', show_upload: false, lightbox_id: '', "
                    "add_title: '', add_url: '', add_description: '', add_category: '', "
                    "cat_name: '', cat_color: 'slate'}"
                ),
            ),

            # Upload form (toggleable)
            upload_form(),

            # Filter bar (category tabs)
            Div(
                filter_bar(),
                class_="mb-4",
            ),

            # Stats
            gallery_stats(),

            # Gallery grid (replaced by SSE)
            Div(
                gallery_grid(),
                class_="mt-4",
            ),

            # Category manager
            Div(
                H2("Categories", class_="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3"),
                category_manager(),
                class_="mt-10 pt-6 border-t border-gray-100",
            ),

            # Multi-tab sync notice
            P(
                "Open in multiple tabs — uploads and deletes sync in real time",
                class_="text-xs text-gray-400 mt-6 text-center",
            ),

            # Lightbox overlay
            lightbox(),

            # SSE connection
            Div(data_init="@get('/sse')", style="display:none"),

            class_="max-w-5xl mx-auto px-6 py-12",
        ),
        title="Nitro Gallery",
        datastar=True,
        tailwind4=True,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Sanic("NitroGallery")
configure_nitro(app)


@app.before_server_start
async def setup(app, loop=None):
    Category.repository().init_db()
    GalleryImage.repository().init_db()
    # Seed default categories
    if not Category.all():
        for cat_data in DEFAULT_CATEGORIES:
            Category(id=cat_data["id"], name=cat_data["name"], color=cat_data["color"]).save()
    # Seed sample images
    if not GalleryImage.all():
        for sample in SAMPLE_IMAGES:
            GalleryImage(
                id=uuid.uuid4().hex[:8],
                title=sample["title"],
                image_url=sample["image_url"],
                description=sample["description"],
                category=sample["category"],
                created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ).save()


@app.get("/")
async def homepage(request: Request):
    return html(str(gallery_page()))


@app.get("/sse")
@datastar_response
async def sse_stream(request: Request):
    """SSE endpoint — Datastar connects here via data_init."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"
    async with Client(client_id=client_id, topics=["sse"]) as client:
        async for msg in client.stream(timeout=60.0):
            yield msg.data


@app.get("/api/image/<image_id>")
async def get_image_for_lightbox(request: Request, image_id: str):
    """Return image detail as SSE patch to populate the lightbox."""
    img = GalleryImage.get(image_id)
    if not img:
        return html("", status=404)
    publish_sync("sse", SSE.patch_elements(lightbox_content(img), selector="#lightbox-content"))
    return html("ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8016, debug=True, auto_reload=True)

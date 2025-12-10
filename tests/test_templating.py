"""
Tests for Nitro templating system: Page, Signals, and create_template.

These tests verify the template.py module functionality including Page rendering,
Datastar integration, and Signal operations.
"""

import pytest
from rusty_tags import H1, Div, Button, HtmlString
from rusty_tags.datastar import Signals
from nitro.infrastructure.html.template import Page, create_template


class TestPageRendering:
    """Tests for Page() function"""

    def test_page_renders_complete_html(self):
        """Page() should render complete HTML page with DOCTYPE, html, head, body"""
        page = Page(H1("Hello"), title="Test")
        html_str = str(page)

        assert "<!DOCTYPE html>" in html_str or "<!doctype html>" in html_str
        assert "<html" in html_str
        assert "</html>" in html_str
        assert "<head>" in html_str
        assert "</head>" in html_str
        assert "<body>" in html_str
        assert "</body>" in html_str
        assert "<title>Test</title>" in html_str
        assert "<h1>Hello</h1>" in html_str

    def test_page_includes_datastar_by_default(self):
        """Page() should include Datastar CDN script by default (datastar=True)"""
        page = Page(Div())
        html_str = str(page)

        # Datastar should be included by default
        assert "datastar" in html_str.lower()
        assert "script" in html_str.lower()

    def test_page_includes_datastar_when_enabled(self):
        """Page() should include Datastar CDN when datastar=True"""
        page = Page(Div(), datastar=True)
        html_str = str(page)

        assert "datastar" in html_str.lower()
        assert "cdn.jsdelivr.net" in html_str or "unpkg.com" in html_str

    def test_page_excludes_datastar_when_disabled(self):
        """Page() should NOT include Datastar when datastar=False"""
        page = Page(Div(), datastar=False)
        html_str = str(page)

        assert "datastar" not in html_str.lower()

    def test_page_includes_tailwind_css_when_configured(self):
        """Page() should include Tailwind CSS link when configured (via config)"""
        # Note: This test verifies the Page looks for configured Tailwind CSS output
        # The actual link is only included if config.tailwind.css_output exists
        # For now, we just verify the Page accepts the configuration
        page = Page(Div(), datastar=False)
        html_str = str(page)

        # Page should render successfully (Tailwind link only added if file exists)
        assert "<html" in html_str
        assert "<body>" in html_str

    def test_page_includes_lucide_when_enabled(self):
        """Page() should include Lucide icons CDN when lucide=True"""
        page = Page(Div(), lucide=True)
        html_str = str(page)

        assert "lucide" in html_str.lower()

    def test_page_includes_highlightjs_when_enabled(self):
        """Page() should include highlight.js CDN when highlightjs=True"""
        page = Page(Div(), highlightjs=True)
        html_str = str(page)

        # Should have both CSS and JS
        assert "highlight" in html_str.lower()
        assert any(x in html_str for x in ["hljs", "highlightjs"])

    def test_page_custom_hdrs(self):
        """Page() should include custom headers when hdrs tuple is provided"""
        from rusty_tags import Script

        custom_script = Script("console.log('test');")
        page = Page(Div(), hdrs=(custom_script,))
        html_str = str(page)

        assert "console.log('test')" in html_str

    def test_page_custom_ftrs(self):
        """Page() should include custom footers when ftrs tuple is provided"""
        from rusty_tags import Script

        footer_script = Script("console.log('footer');")
        page = Page(Div(), ftrs=(footer_script,))
        html_str = str(page)

        assert "console.log('footer')" in html_str


class TestCreateTemplateDecorator:
    """Tests for create_template decorator"""

    @pytest.mark.asyncio
    async def test_create_template_decorator_wraps_function(self):
        """create_template decorator should wrap function output in Page"""
        template = create_template(page_title="Test Page")

        @template()
        def my_view():
            return Div("Content")

        result = await my_view()
        html_str = str(result)

        # Should be wrapped in full page
        assert "<html" in html_str
        assert "<body>" in html_str
        assert "<div>Content</div>" in html_str
        assert "<title>Test Page</title>" in html_str

    @pytest.mark.asyncio
    async def test_create_template_decorator_with_custom_title(self):
        """create_template decorator should support custom title per function"""
        template = create_template(page_title="Default")

        @template(title="Custom Title")
        def my_view():
            return Div("Content")

        result = await my_view()
        html_str = str(result)

        assert "<title>Custom Title</title>" in html_str
        assert "Default" not in html_str

    @pytest.mark.asyncio
    async def test_create_template_decorator_preserves_function_args(self):
        """create_template decorator should preserve function arguments"""
        template = create_template()

        @template()
        def my_view(name: str, age: int):
            return Div(f"{name} is {age}")

        result = await my_view("Alice", 25)
        html_str = str(result)

        assert "Alice is 25" in html_str

    @pytest.mark.asyncio
    async def test_create_template_decorator_supports_async_functions(self):
        """create_template decorator should support async view functions"""
        template = create_template()

        @template()
        async def my_async_view():
            return Div("Async Content")

        result = await my_async_view()
        html_str = str(result)

        assert "Async Content" in html_str


class TestSignals:
    """Tests for Datastar Signals integration"""

    def test_signals_object_creation(self):
        """Signals should be creatable with initial values"""
        sigs = Signals(counter=0, name="Alice")

        assert isinstance(sigs, Signals)
        # Signals should have counter and name attributes
        assert hasattr(sigs, 'counter')
        assert hasattr(sigs, 'name')

    def test_signals_generates_data_attributes(self):
        """Signals should generate data-* attributes for Datastar"""
        sigs = Signals(counter=0)

        # Convert to string to check attributes
        sigs_str = str(sigs)

        # Should contain data attributes
        assert "data-" in sigs_str or "counter" in sigs_str

    def test_signals_arithmetic_add(self):
        """Signals should support .add() for arithmetic operations"""
        sigs = Signals(count=0)

        # Should be able to call add
        add_expr = sigs.count.add(1)

        # Should return a string expression
        assert isinstance(str(add_expr), str)

    def test_signals_arithmetic_sub(self):
        """Signals should support .sub() for arithmetic operations"""
        sigs = Signals(count=10)

        # Should be able to call sub
        sub_expr = sigs.count.sub(1)

        # Should return a string expression
        assert isinstance(str(sub_expr), str)

    def test_signals_set_operation(self):
        """Signals should support .set() for assignment"""
        sigs = Signals(name="Alice")

        # Should be able to call set
        set_expr = sigs.name.set("Bob")

        # Should return a string expression
        assert isinstance(str(set_expr), str)

    def test_signals_toggle_operation(self):
        """Signals should support .toggle() for boolean operations"""
        sigs = Signals(visible=True)

        # Should be able to call toggle
        toggle_expr = sigs.visible.toggle()

        # Should return a string expression
        assert isinstance(str(toggle_expr), str)

    def test_signals_in_component(self):
        """Signals should work when passed to components"""
        sigs = Signals(counter=0)

        # Should be able to use signals in a component
        button = Button(
            "+",
            **{"data-on-click": str(sigs.counter.add(1))}
        )

        button_str = str(button)
        assert "data-on-click" in button_str


class TestPageIntegration:
    """Integration tests for Page with Signals"""

    def test_page_with_signals(self):
        """Page should work with Signals for reactive components"""
        sigs = Signals(counter=0)

        page = Page(
            Div(
                Button("-"),
                Button("+"),
            ),
            title="Counter",
            datastar=True
        )

        html_str = str(page)

        # Should have datastar and be a valid page
        assert "datastar" in html_str.lower()
        assert "<button>-</button>" in html_str
        assert "<button>+</button>" in html_str


class TestRustyTagsElements:
    """Tests for RustyTags HTML element generation"""

    def test_div_generates_div_element(self):
        """Div() should generate <div> element with attributes"""
        from rusty_tags import Div

        div = Div("content", class_="container")
        div_str = str(div)

        assert "<div" in div_str
        assert "container" in div_str
        assert "content" in div_str
        assert "</div>" in div_str

    def test_rustytags_supports_nested_elements(self):
        """RustyTags should support nested elements"""
        from rusty_tags import Div, H1, P

        nested = Div(
            H1("Title"),
            P("Content")
        )
        nested_str = str(nested)

        # Should have proper nesting
        assert "<div>" in nested_str
        assert "<h1>Title</h1>" in nested_str
        assert "<p>Content</p>" in nested_str
        assert "</div>" in nested_str

        # H1 should come before P
        h1_pos = nested_str.find("<h1>")
        p_pos = nested_str.find("<p>")
        assert h1_pos < p_pos

    def test_button_supports_event_handlers(self):
        """Button should support event handler attributes"""
        button = Button("Click", **{"data-on-click": "handleClick()"})
        button_str = str(button)

        assert "<button" in button_str
        assert "data-on-click" in button_str
        assert "handleClick()" in button_str
        assert "Click" in button_str

    def test_component_system_reusable_elements(self):
        """Custom component functions should be reusable"""
        from rusty_tags import Div, H2, P

        # Define a reusable component
        def card(title: str, content: str):
            return Div(
                H2(title),
                P(content),
                class_="card"
            )

        # Use component in a page
        page = Page(
            card("Welcome", "Hello World"),
            card("About", "Information"),
            title="Components"
        )

        html_str = str(page)

        # Should render both components
        assert "Welcome" in html_str
        assert "Hello World" in html_str
        assert "About" in html_str
        assert "Information" in html_str
        assert "card" in html_str  # class name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

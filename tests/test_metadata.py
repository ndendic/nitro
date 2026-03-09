# nitro/tests/test_metadata.py
import pytest
from nitro.routing.metadata import ActionMetadata, extract_parameters, set_action_metadata, get_action_metadata, has_action_metadata


class TestActionMetadata:
    def test_defaults(self):
        meta = ActionMetadata()
        assert meta.method == "POST"
        assert meta.status_code == 200
        assert meta.event_name == ""
        assert meta.prefix == ""

    def test_method_uppercase(self):
        meta = ActionMetadata(method="get")
        assert meta.method == "GET"

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            ActionMetadata(method="INVALID")

    def test_event_name_stored(self):
        meta = ActionMetadata(event_name="Counter.increment")
        assert meta.event_name == "Counter.increment"

    def test_prefix_stored(self):
        meta = ActionMetadata(prefix="auth")
        assert meta.prefix == "auth"

    def test_no_generate_url_path(self):
        """generate_url_path has been removed."""
        meta = ActionMetadata()
        assert not hasattr(meta, "generate_url_path")


class TestMetadataHelpers:
    def test_set_and_get(self):
        def foo(): pass
        meta = ActionMetadata(function_name="foo")
        set_action_metadata(foo, meta)
        assert get_action_metadata(foo) is meta

    def test_has_metadata(self):
        def bar(): pass
        assert has_action_metadata(bar) is False
        set_action_metadata(bar, ActionMetadata())
        assert has_action_metadata(bar) is True

    def test_get_returns_none_if_absent(self):
        def baz(): pass
        assert get_action_metadata(baz) is None


class TestExtractParameters:
    def test_simple_function(self):
        def fn(name: str, age: int = 25): pass
        params = extract_parameters(fn)
        assert "name" in params
        assert params["name"]["annotation"] is str
        assert params["name"]["default"] is None
        assert params["age"]["default"] == 25

    def test_self_param(self):
        class Foo:
            def bar(self, x: int): pass
        params = extract_parameters(Foo.bar)
        assert "self" in params

    def test_no_annotations(self):
        def fn(x, y): pass
        params = extract_parameters(fn)
        assert params["x"]["annotation"] is None

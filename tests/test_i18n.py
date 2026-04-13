"""Tests for nitro.i18n — internationalization and localization."""

import json
from pathlib import Path

import pytest

from nitro.i18n import (
    Catalog,
    Translations,
    configure_i18n,
    format_message,
    get_locale,
    pluralize,
    set_locale,
    t,
)
from nitro.i18n.integration import negotiate_locale, parse_accept_language


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_translations():
    """Reset global translations between tests."""
    Translations.reset()
    yield
    Translations.reset()


@pytest.fixture
def locales_dir(tmp_path):
    """Create a temp directory with locale JSON files."""
    en = {"hello": "Hello!", "nav": {"home": "Home", "about": "About"}}
    sr = {"hello": "Zdravo!", "nav": {"home": "Početna", "about": "O nama"}}

    (tmp_path / "en.json").write_text(json.dumps(en))
    (tmp_path / "sr.json").write_text(json.dumps(sr))
    return tmp_path


# ── Catalog ───────────────────────────────────────────────────────────────


class TestCatalog:
    def test_add_and_get(self):
        c = Catalog("en")
        c.add("hello", "Hello!")
        assert c.get("hello") == "Hello!"

    def test_get_missing_returns_none(self):
        c = Catalog("en")
        assert c.get("missing") is None

    def test_has(self):
        c = Catalog("en")
        c.add("hello", "Hello!")
        assert c.has("hello")
        assert not c.has("missing")

    def test_add_many(self):
        c = Catalog("en")
        c.add_many({"a": "A", "b": "B"})
        assert c.get("a") == "A"
        assert c.get("b") == "B"

    def test_keys(self):
        c = Catalog("en")
        c.add_many({"x": "X", "y": "Y"})
        assert sorted(c.keys()) == ["x", "y"]

    def test_len(self):
        c = Catalog("en")
        assert len(c) == 0
        c.add("x", "X")
        assert len(c) == 1

    def test_repr(self):
        c = Catalog("en")
        c.add("x", "X")
        assert repr(c) == "Catalog('en', 1 keys)"

    def test_merge(self):
        c1 = Catalog("en")
        c1.add("a", "A1")
        c1.add("b", "B1")

        c2 = Catalog("en")
        c2.add("b", "B2")
        c2.add("c", "C2")

        c1.merge(c2)
        assert c1.get("a") == "A1"
        assert c1.get("b") == "B2"  # c2 wins
        assert c1.get("c") == "C2"

    def test_from_dict_flat(self):
        c = Catalog.from_dict("en", {"hello": "Hello!", "bye": "Bye!"})
        assert c.get("hello") == "Hello!"
        assert c.get("bye") == "Bye!"

    def test_from_dict_nested(self):
        c = Catalog.from_dict("en", {
            "nav": {"home": "Home", "about": "About"},
            "hello": "Hello!",
        })
        assert c.get("nav.home") == "Home"
        assert c.get("nav.about") == "About"
        assert c.get("hello") == "Hello!"

    def test_from_dict_deeply_nested(self):
        c = Catalog.from_dict("en", {
            "a": {"b": {"c": "deep"}},
        })
        assert c.get("a.b.c") == "deep"


# ── Pluralization ─────────────────────────────────────────────────────────


class TestPluralize:
    def test_english_singular(self):
        assert pluralize("{count} item|{count} items", 1) == "1 item"

    def test_english_plural(self):
        assert pluralize("{count} item|{count} items", 0) == "0 items"
        assert pluralize("{count} item|{count} items", 5) == "5 items"

    def test_single_form(self):
        assert pluralize("things", 5) == "things"

    def test_slavic_singular(self):
        # 1 stavka
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 1, locale="sr") == "1 stavka"

    def test_slavic_few(self):
        # 2-4 stavke
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 2, locale="sr") == "2 stavke"
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 3, locale="sr") == "3 stavke"
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 4, locale="sr") == "4 stavke"

    def test_slavic_many(self):
        # 5+ stavki
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 5, locale="sr") == "5 stavki"
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 11, locale="sr") == "11 stavki"
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 0, locale="sr") == "0 stavki"

    def test_slavic_21(self):
        # 21 is singular again in Slavic
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 21, locale="sr") == "21 stavka"

    def test_slavic_22(self):
        assert pluralize("{count} stavka|{count} stavke|{count} stavki", 22, locale="sr") == "22 stavke"

    def test_slavic_teens(self):
        # 11-14 are always form 2 (many)
        for n in [11, 12, 13, 14]:
            result = pluralize("{count} stavka|{count} stavke|{count} stavki", n, locale="sr")
            assert result == f"{n} stavki", f"Failed for count={n}"

    def test_russian_uses_slavic_rules(self):
        assert pluralize("{count} файл|{count} файла|{count} файлов", 1, locale="ru") == "1 файл"
        assert pluralize("{count} файл|{count} файла|{count} файлов", 3, locale="ru") == "3 файла"
        assert pluralize("{count} файл|{count} файла|{count} файлов", 5, locale="ru") == "5 файлов"


# ── Format Message ────────────────────────────────────────────────────────


class TestFormatMessage:
    def test_basic(self):
        assert format_message("Hello, {name}!", name="World") == "Hello, World!"

    def test_multiple_args(self):
        assert format_message("{a} + {b} = {c}", a=1, b=2, c=3) == "1 + 2 = 3"

    def test_no_args(self):
        assert format_message("No args") == "No args"

    def test_missing_key_graceful(self):
        result = format_message("Hello, {name}!", age=25)
        # Should not crash, returns what it can
        assert "Hello" in result


# ── Translations ──────────────────────────────────────────────────────────


class TestTranslations:
    def test_basic_translate(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        assert tr.translate("hello") == "Hello!"

    def test_locale_switching(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        tr.load_dict("sr", {"hello": "Zdravo!"})

        assert tr.translate("hello") == "Hello!"
        tr.set_locale("sr")
        assert tr.translate("hello") == "Zdravo!"

    def test_fallback_locale(self):
        tr = Translations(default_locale="sr", fallback_locale="en")
        tr.load_dict("en", {"hello": "Hello!", "only_en": "English only"})
        tr.load_dict("sr", {"hello": "Zdravo!"})

        tr.set_locale("sr")
        assert tr.translate("hello") == "Zdravo!"
        assert tr.translate("only_en") == "English only"  # falls back to en

    def test_missing_key_returns_key(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        assert tr.translate("missing") == "missing"

    def test_missing_key_with_default(self):
        tr = Translations()
        tr.load_dict("en", {})
        assert tr.translate("missing", default="Fallback") == "Fallback"

    def test_with_formatting(self):
        tr = Translations()
        tr.load_dict("en", {"greeting": "Hello, {name}!"})
        assert tr.translate("greeting", name="Nikola") == "Hello, Nikola!"

    def test_with_pluralization(self):
        tr = Translations()
        tr.load_dict("en", {"items": "{count} item|{count} items"})
        assert tr.translate("items", count=1) == "1 item"
        assert tr.translate("items", count=5) == "5 items"

    def test_slavic_pluralization_in_translate(self):
        tr = Translations(default_locale="sr")
        tr.load_dict("sr", {"items": "{count} stavka|{count} stavke|{count} stavki"})
        tr.set_locale("sr")
        assert tr.translate("items", count=1) == "1 stavka"
        assert tr.translate("items", count=3) == "3 stavke"
        assert tr.translate("items", count=5) == "5 stavki"

    def test_locale_override_per_call(self):
        tr = Translations(default_locale="en")
        tr.load_dict("en", {"hello": "Hello!"})
        tr.load_dict("sr", {"hello": "Zdravo!"})

        assert tr.translate("hello") == "Hello!"
        assert tr.translate("hello", locale="sr") == "Zdravo!"
        assert tr.locale == "en"  # didn't change global

    def test_has_key(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        assert tr.has_key("hello")
        assert not tr.has_key("missing")

    def test_has_key_specific_locale(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        tr.load_dict("sr", {"hello": "Zdravo!"})
        assert tr.has_key("hello", locale="sr")
        assert not tr.has_key("hello", locale="de")

    def test_available_locales(self):
        tr = Translations()
        tr.load_dict("en", {"a": "A"})
        tr.load_dict("sr", {"a": "A"})
        assert sorted(tr.available_locales) == ["en", "sr"]

    def test_load_json(self, tmp_path):
        data = {"greeting": "Hallo!", "nav": {"home": "Startseite"}}
        path = tmp_path / "de.json"
        path.write_text(json.dumps(data))

        tr = Translations()
        tr.load_json("de", path)
        tr.set_locale("de")
        assert tr.translate("greeting") == "Hallo!"
        assert tr.translate("nav.home") == "Startseite"

    def test_load_dir(self, locales_dir):
        tr = Translations()
        tr.load_dir(locales_dir)
        assert "en" in tr.available_locales
        assert "sr" in tr.available_locales
        assert tr.translate("hello", locale="en") == "Hello!"
        assert tr.translate("hello", locale="sr") == "Zdravo!"

    def test_merge_on_reload(self):
        tr = Translations()
        tr.load_dict("en", {"a": "A1", "b": "B1"})
        tr.load_dict("en", {"b": "B2", "c": "C2"})
        assert tr.translate("a") == "A1"
        assert tr.translate("b") == "B2"
        assert tr.translate("c") == "C2"


# ── Global t() Function ──────────────────────────────────────────────────


class TestGlobalT:
    def test_t_basic(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})
        assert t("hello") == "Hello!"

    def test_t_without_instance_raises(self):
        with pytest.raises(RuntimeError, match="No Translations instance"):
            t("hello")

    def test_t_with_formatting(self):
        tr = Translations()
        tr.load_dict("en", {"greet": "Hi, {name}!"})
        assert t("greet", name="World") == "Hi, World!"

    def test_t_with_count(self):
        tr = Translations()
        tr.load_dict("en", {"items": "{count} thing|{count} things"})
        assert t("items", count=1) == "1 thing"
        assert t("items", count=3) == "3 things"

    def test_t_with_locale_override(self):
        tr = Translations()
        tr.load_dict("en", {"hi": "Hi!"})
        tr.load_dict("de", {"hi": "Hallo!"})
        assert t("hi") == "Hi!"
        assert t("hi", locale="de") == "Hallo!"


# ── Accept-Language Parsing ───────────────────────────────────────────────


class TestParseAcceptLanguage:
    def test_single_locale(self):
        assert parse_accept_language("en") == ["en"]

    def test_multiple_with_quality(self):
        result = parse_accept_language("sr-Latn,en;q=0.8,de;q=0.5")
        assert result == ["sr-Latn", "en", "de"]

    def test_quality_ordering(self):
        result = parse_accept_language("de;q=0.5,en;q=0.9,fr;q=0.1")
        assert result == ["en", "de", "fr"]

    def test_empty_string(self):
        assert parse_accept_language("") == []

    def test_complex_header(self):
        result = parse_accept_language("en-US,en;q=0.9,sr;q=0.8")
        assert result[0] == "en-US"
        assert "sr" in result


# ── Locale Negotiation ────────────────────────────────────────────────────


class TestNegotiateLocale:
    def test_exact_match(self):
        assert negotiate_locale(["sr", "en"], ["en", "sr", "de"]) == "sr"

    def test_base_language_match(self):
        assert negotiate_locale(["en-US"], ["en", "de"]) == "en"

    def test_no_match_returns_default(self):
        assert negotiate_locale(["ja"], ["en", "de"], default="en") == "en"

    def test_priority_order(self):
        assert negotiate_locale(["de", "en"], ["en", "de"]) == "de"


# ── Integration ───────────────────────────────────────────────────────────


class TestConfigureI18n:
    def test_sanic_like_app(self, locales_dir):
        class FakeCtx:
            pass

        class FakeApp:
            ctx = FakeCtx()
            _handlers: list = []

            def on_request(self, fn):
                self._handlers.append(fn)
                return fn

        app = FakeApp()
        tr = configure_i18n(app, locales_dir, default_locale="en")

        assert app.ctx.translations is tr
        assert "en" in tr.available_locales
        assert "sr" in tr.available_locales
        assert len(app._handlers) == 1

    def test_set_and_get_locale(self):
        tr = Translations()
        tr.load_dict("en", {"hello": "Hello!"})

        set_locale("sr")
        assert get_locale() == "sr"

        set_locale("en")
        assert get_locale() == "en"

    def test_get_locale_default(self):
        set_locale("")  # clear any prior context var
        Translations(default_locale="de")
        # get_locale without set_locale should return the default
        assert get_locale() == "de"


# ── End-to-End ────────────────────────────────────────────────────────────


class TestEndToEnd:
    def test_full_workflow(self, locales_dir):
        # Load translations
        tr = Translations(default_locale="en", fallback_locale="en")
        tr.load_dir(locales_dir)

        # Add pluralization
        tr.load_dict("en", {"items": "{count} item|{count} items"})
        tr.load_dict("sr", {"items": "{count} stavka|{count} stavke|{count} stavki"})

        # English
        tr.set_locale("en")
        assert t("hello") == "Hello!"
        assert t("nav.home") == "Home"
        assert t("items", count=1) == "1 item"
        assert t("items", count=5) == "5 items"

        # Serbian
        tr.set_locale("sr")
        assert t("hello") == "Zdravo!"
        assert t("nav.home") == "Početna"
        assert t("items", count=1) == "1 stavka"
        assert t("items", count=3) == "3 stavke"
        assert t("items", count=5) == "5 stavki"

        # Missing key falls back to English
        assert t("nav.about") == "O nama"  # exists in sr
        tr.load_dict("en", {"only_en": "Only in English"})
        assert t("only_en") == "Only in English"  # falls back

    def test_multilingual_app_simulation(self, locales_dir):
        tr = Translations(default_locale="en", fallback_locale="en")
        tr.load_dir(locales_dir)

        # Simulate request with Accept-Language
        header = "sr,en;q=0.8"
        preferred = parse_accept_language(header)
        locale = negotiate_locale(preferred, tr.available_locales)

        assert locale == "sr"
        assert t("hello", locale=locale) == "Zdravo!"

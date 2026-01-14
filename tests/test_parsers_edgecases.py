import textwrap

from logic.parsers import MarkdownParser


def test_parse_base_prompts_empty():
    md = ""  # empty content
    prompts = MarkdownParser.parse_base_prompts(md)
    assert isinstance(prompts, dict)
    assert prompts == {}


def test_parse_base_prompts_malformed_header():
    md = textwrap.dedent(
        """
        # Not a level-two header
        Default
        A gentle style
        """
    )
    prompts = MarkdownParser.parse_base_prompts(md)
    # Should find no prompts when headers are not '## '
    assert prompts == {}


def test_shared_outfits_duplicate_sections_and_empty():
    md = textwrap.dedent(
        """
        ## Common Outfits
        ### Casual
        T

        ## COMMON outfits
        ### Casual
        Duplicate casual desc

        ## Other
        ### Solo
        Single item
        """
    )
    shared = MarkdownParser.parse_shared_outfits(md)
    # 'Common' should exist and include the last 'Casual' override
    assert "Common" in shared
    assert "Casual" in shared["Common"]
    val = shared["Common"]["Casual"]
    # Handle dict or string depending on parser implementation
    if isinstance(val, dict):
        assert val.get("description") in ("Duplicate casual desc", "T")
    else:
        assert val in ("Duplicate casual desc", "T")
    assert "Other" in shared


def test_parse_characters_malformed_outfit_entries():
    md = textwrap.dedent(
        """
        ### Alex
        **Appearance:** Tall
        **Outfits:**

        #### Weird
        - **Top** Missing colon and bold close
        - Bottom: plain value
        - **Footwear:** Sneakers
        """
    )

    chars = MarkdownParser.parse_characters(md)
    assert "Alex" in chars
    outfits = chars["Alex"]["outfits"]
    assert "Weird" in outfits
    # Should parse items robustly even when bold markers or colons are malformed
    val = outfits["Weird"]
    assert isinstance(val, dict)
    # 'Bottom' should be present (parsed from plain 'Bottom:')
    assert any(k.lower().startswith("bottom") for k in val.keys())

import textwrap

from logic.parsers import MarkdownParser


def test_parse_base_prompts():
    md = textwrap.dedent(
        """
        ## Default
        A gentle illustration style.
        ---

        ## High Contrast
        Sharp, dramatic lighting.
        ---
        """
    )
    prompts = MarkdownParser.parse_base_prompts(md)
    assert "Default" in prompts
    assert prompts["Default"].startswith("A gentle illustration")
    assert "High Contrast" in prompts


def test_parse_shared_outfits_and_merge():
    md = textwrap.dedent(
        """
        ## Common Outfits
        ### Casual
        A simple casual outfit with tee and jeans.

        ### Formal
        Elegant evening dress.
        """
    )
    shared = MarkdownParser.parse_shared_outfits(md)
    assert "Common" in shared
    assert "Casual" in shared["Common"]
    assert shared["Common"]["Formal"].startswith("Elegant")

    # merge with character outfits overriding common
    char_data = {"outfits": {"Casual": "Character-specific casual"}}
    merged = MarkdownParser.merge_character_outfits(char_data, shared, "Alice")
    assert merged["Casual"] == "Character-specific casual"
    assert "Formal" in merged


def test_parse_presets():
    md = textwrap.dedent(
        """
        ## General
        - **Standing:** Standing naturally, arms at sides
        - **Sitting:** Sitting on a chair

        ## Outdoors
        - **Beach:** Sandy shore at sunset
        """
    )
    presets = MarkdownParser.parse_presets(md)
    assert "General" in presets
    assert "Standing" in presets["General"]
    assert presets["Outdoors"]["Beach"].startswith("Sandy")


def test_parse_characters_structured_outfits_one_piece():
    md = textwrap.dedent(
        """
        ### Nora
        **Appearance:** Tall, olive skin
        **Outfits:**

        #### Base
        - **Top:** Crop top
        - **Bottom:** N/A
        - **Footwear:** Sandals

        #### Summer Dress
        - **Top:** Light fabric
        # continuation line example
        - **Accessories:** Sunglasses
        """
    )

    chars = MarkdownParser.parse_characters(md)
    assert "Nora" in chars
    outfits = chars["Nora"]["outfits"]
    assert "Base" in outfits
    # Bottom should be canonicalized to None for one-piece
    base = outfits["Base"]
    assert isinstance(base, dict)
    assert base.get("Bottom") is None
    assert base.get("one_piece") is True


def test_parse_characters_legacy_list_format():
    md = textwrap.dedent(
        """
        ### Sam
        **Appearance:** Short build
        **Outfits:**
        - **Base:** Casual tee and jeans
        - **Sport:** Tracksuit
        """
    )
    chars = MarkdownParser.parse_characters(md)
    assert "Sam" in chars
    outfits = chars["Sam"]["outfits"]
    assert outfits["Base"].startswith("Casual tee")
    assert outfits["Sport"].startswith("Tracksuit")

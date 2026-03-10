from __future__ import annotations

from reach.forge.api import generate_generator


def test_xss_zero_width_generator_returns_eval_wrapper() -> None:
    output = generate_generator(
        "xss_zero_width",
        payload='<script>alert("flag: test-flag");</script>',
    )

    assert output.kind == "xss_zero_width"
    assert output.metadata["family"] == "xss"
    assert output.value.startswith('eval("')
    assert '.replace(/./g,c=>+!(c=="\u200b"))' in output.value
    assert "alert" not in output.value
    assert "test-flag" not in output.value


def test_xss_zero_width_generator_can_wrap_script_tags() -> None:
    output = generate_generator(
        "xss_zero_width",
        payload='alert("flag: wrapped")',
        tags=True,
    )

    assert output.value.startswith('eval("')
    assert "<script>" not in output.value
    assert "wrapped" not in output.value

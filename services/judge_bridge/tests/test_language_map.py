from services.judge_bridge.app.domain.language_map import PRODUCT_LANGUAGE_IDS


def test_language_map_covers_the_launch_languages():
    assert set(PRODUCT_LANGUAGE_IDS) == {
        "c",
        "cpp",
        "java",
        "python",
        "javascript",
        "typescript",
        "go",
        "rust",
    }

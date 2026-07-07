import respx
from httpx import Response

from pre_screen_common.ai_client import AIClient


@respx.mock
def test_ai_client_uses_openai_compatible_chat_endpoint():
    route = respx.post("https://aiapi.szmckj.cn/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )
    )

    client = AIClient(api_key="test-key", base_url="https://aiapi.szmckj.cn", model="qwen3.6-35b-a3b")
    result = client.simple_text_completion("ping")

    assert route.called
    assert result == "pong"


@respx.mock
def test_ai_client_preserves_custom_prefix_base_urls():
    route = respx.post("https://aiapi.szmckj.cn/api/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )
    )

    client = AIClient(api_key="test-key", base_url="https://aiapi.szmckj.cn/api", model="qwen3.6-35b-a3b")
    result = client.simple_text_completion("ping")

    assert route.called
    assert result == "pong"


@respx.mock
def test_ai_client_sends_multimodal_messages_to_openai_compatible_endpoint():
    route = respx.post("http://172.16.99.204:3398/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [{"message": {"content": '{"markdown":"ok"}'}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )
    )

    client = AIClient(api_key="test-key", base_url="http://172.16.99.204:3398", model="qwen3.6-27b")
    result = client.multimodal_completion(
        prompt="read this resume",
        image_data_urls=["data:image/png;base64,AAAA"],
    )

    assert route.called
    payload = route.calls.last.request.read()
    assert b"qwen3.6-27b" in payload
    assert b"image_url" in payload
    assert result == '{"markdown":"ok"}'

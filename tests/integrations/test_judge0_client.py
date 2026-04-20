import respx
from httpx import Response

from pre_screen_common.judge0_client import Judge0Client


@respx.mock
def test_judge0_client_fetches_supported_languages():
    route = respx.get("http://judge0:2358/languages").mock(
        return_value=Response(200, json=[{"id": 71, "name": "Python (3.8.1)"}])
    )

    client = Judge0Client(base_url="http://judge0:2358")
    languages = client.list_languages()

    assert route.called
    assert languages[0]["name"] == "Python (3.8.1)"

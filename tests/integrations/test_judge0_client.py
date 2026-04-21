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


@respx.mock
def test_judge0_client_runs_submission_sync():
    route = respx.post("http://judge0:2358/submissions?wait=true").mock(
        return_value=Response(
            201,
            json={
                "token": "abc123",
                "stdout": "hello from judge0\n",
                "stderr": None,
                "compile_output": None,
                "message": None,
                "status": {"id": 3, "description": "Accepted"},
            },
        )
    )

    client = Judge0Client(base_url="http://judge0:2358")
    result = client.run_sync({"language_id": 71, "source_code": "print('hello from judge0')"})

    assert route.called
    assert result["stdout"] == "hello from judge0\n"
    assert result["status"]["id"] == 3

from pre_screen_common.security import hash_password, hash_token, verify_password


def test_password_hash_roundtrip():
    password_hash = hash_password("demo-pass")
    assert password_hash.startswith("pbkdf2_sha256$")
    assert verify_password("demo-pass", password_hash)
    assert not verify_password("wrong", password_hash)


def test_token_hash_is_stable():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")

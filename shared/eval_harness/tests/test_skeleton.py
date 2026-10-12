import eval_harness


def test_package_imports() -> None:
    assert isinstance(eval_harness.__doc__, str)

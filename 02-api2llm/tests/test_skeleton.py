import api2llm


def test_package_imports() -> None:
    assert isinstance(api2llm.__doc__, str)

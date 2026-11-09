from labeler.python_version_check import python_too_old, python_version_message


def test_old_python_is_too_old():
    assert python_too_old((3, 8, 5))
    assert python_too_old((3, 11, 9))


def test_supported_python_is_fine():
    assert not python_too_old((3, 12, 0))
    assert not python_too_old((3, 13, 1))


def test_message_names_both_versions_and_the_start_command():
    message = python_version_message((3, 8, 5))
    assert "3.8.5" in message and "3.12" in message
    assert ".venv/bin/python -m streamlit run app.py" in message

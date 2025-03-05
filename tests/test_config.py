import tempfile
import os
import pytest
from ai_debugger.config import Config


def test_default_config():
    config = Config()
    assert config.get("models.default") == "microsoft/CodeGPT-small-py"
    assert config.get("max_file_size_mb") == 5


def test_custom_config():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write("""
        models:
            default: test-model
        max_file_size_mb: 10
        """)
        temp_path = temp.name

    try:
        config = Config(config_path=temp_path)
        assert config.get("models.default") == "test-model"
        assert config.get("max_file_size_mb") == 10
        assert config.get("models.large") == "microsoft/CodeBERT-base"
    finally:
        os.unlink(temp_path)


def test_set_and_save():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
        temp_path = temp.name

    try:
        config = Config()
        config.set("models.default", "new-model")
        config.set("new_option", "value")

        # Save and reload
        config.save(config_path=temp_path)
        new_config = Config(config_path=temp_path)

        assert new_config.get("models.default") == "new-model"
        assert new_config.get("new_option") == "value"
    finally:
        os.unlink(temp_path)

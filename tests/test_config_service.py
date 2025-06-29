# desktop_center/tests/test_config_service.py
import pytest
import configparser
from pathlib import Path
from src.services.config_service import ConfigService

# 使用 pytest 的 tmp_path fixture 来创建一个临时目录进行测试
@pytest.fixture
def temp_config_file(tmp_path: Path) -> str:
    config_content = """
[General]
app_name = Test App
start_minimized = true

[InfoService]
host = 127.0.0.1
port = 8080
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content, encoding='utf-8')
    return str(config_file)

def test_load_config_successfully(temp_config_file):
    """测试是否能成功加载一个有效的配置文件。"""
    service = ConfigService(temp_config_file)
    assert service.get_value("General", "app_name") == "Test App"
    assert service.get_value("InfoService", "port") == "8080"

def test_get_value_with_fallback():
    """测试当值不存在时，fallback机制是否正常工作。"""
    service = ConfigService("non_existent_file.ini")
    fallback_value = "default_value"
    assert service.get_value("NoSection", "NoOption", fallback=fallback_value) == fallback_value

def test_set_and_save_value(tmp_path: Path):
    """测试设置新值并保存后，文件内容是否被正确更新。"""
    config_file = tmp_path / "test_save.ini"
    service = ConfigService(str(config_file))

    # 设置一个新值
    service.set_option("NewSection", "NewOption", "NewValue")
    save_result = service.save_config()
    assert save_result is True
    assert config_file.exists()

    # 重新加载并验证
    parser = configparser.ConfigParser()
    parser.read(str(config_file))
    assert parser.get("NewSection", "NewOption") == "NewValue"

def test_handle_non_existent_file():
    """测试当配置文件不存在时，服务是否能正常初始化而不崩溃。"""
    service = ConfigService("non_existent_file.ini")
    assert service.get_sections() == []

def test_get_options_for_section(temp_config_file):
    """测试获取一个section下的所有options。"""
    service = ConfigService(temp_config_file)
    options = service.get_options("General")
    assert ("app_name", "Test App") in options
    assert ("start_minimized", "true") in options
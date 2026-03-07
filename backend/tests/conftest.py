"""Pytest fixtures"""
import os
import tempfile
from pathlib import Path

import pytest

# 确保 backend 在 path 中
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_image_bytes():
    """最小有效 PNG 1x1 像素"""
    return (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )


@pytest.fixture
def sample_image_path(sample_image_bytes):
    """创建临时 PNG 文件路径"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(sample_image_bytes)
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass

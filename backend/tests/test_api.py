"""
后端 API 单测
运行: cd backend && pytest tests/ -v
"""
import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# 在导入 main 前设置环境，避免 config 加载失败
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def _ensure_config():
    """确保 config.json 存在（测试用）"""
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if not config_path.exists():
        config_path.write_text('{"api_config":{"qwen_api_key":"test-key"},"user_info":{}}', encoding='utf-8')


@pytest.fixture(scope="module")
def client():
    _ensure_config()
    from main import app
    return TestClient(app)


# ---------- 健康检查 ----------
def test_health(client):
    """健康检查接口"""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_root(client):
    """根路径"""
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert data.get("status") == "running"


# ---------- 备忘录分析（mock Qwen） ----------
def test_memo_analyze_success(client, sample_image_bytes):
    """备忘录分析 - 成功（mock Qwen 返回）"""
    mock_result = {
        "data_overview": {"distance": 20, "avg_pace": "4'30\""},
        "performance_evaluation": {"text": "表现良好"},
        "improvement_suggestions": ["建议1", "建议2"],
    }
    with patch("app.api.memo.analyze_coros_image", return_value=mock_result):
        r = client.post(
            "/api/memo/analyze",
            data={"memo_text": "今日20K"},
            files={"image": ("test.png", io.BytesIO(sample_image_bytes), "image/png")},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "data_overview" in data
    assert data["data_overview"].get("distance") == 20


def test_memo_analyze_no_image(client):
    """备忘录分析 - 未上传图片应返回 422"""
    r = client.post(
        "/api/memo/analyze",
        data={"memo_text": "今日20K"},
        # 不传 image
    )
    assert r.status_code == 422


def test_memo_save_with_chinese_keys(client, sample_image_bytes):
    """保存时支持 AI 返回的中文键名 data_overview"""
    analysis = {
        "data_overview": {
            "距离": "14.00 km",
            "运动时间": "1小时7分13秒",
            "平均配速": "4'48\"/km",
            "平均心率": "124 bpm",
            "最大心率": "139 bpm",
        },
        "performance_evaluation": {"整体评价": "表现良好"},
        "improvement_suggestions": ["建议1"],
    }
    r = client.post(
        "/api/memo/save",
        data={
            "memo_text": "今日20K",
            "image_path": "/tmp/test.png",
            "analysis_result": json.dumps(analysis),
            "run_date": "2025-03-01",
            "run_type": "aerobic",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "record_id" in data
    # 验证记录详情含 run_score
    rid = data["record_id"]
    detail = client.get(f"/api/records/{rid}").json()
    assert detail["run_date"] == "2025-03-01"
    assert detail["run_type"] == "aerobic"
    assert detail["run_score"] is not None and detail["run_score"] > 0


def test_memo_analyze_qwen_dict_response(client, sample_image_bytes):
    """备忘录分析 - Qwen 返回 dict 格式 content（修复 'dict' has no attribute 'text'）"""
    mock_result = {
        "data_overview": {"distance": 15},
        "performance_evaluation": {"text": "ok"},
        "improvement_suggestions": [],
    }
    with patch("app.api.memo.analyze_coros_image", return_value=mock_result):
        r = client.post(
            "/api/memo/analyze",
            data={"memo_text": ""},
            files={"image": ("x.png", io.BytesIO(sample_image_bytes), "image/png")},
        )
    assert r.status_code == 200
    assert r.json()["success"] is True


# ---------- 历史记录 ----------
def test_records_list(client):
    """历史记录列表"""
    r = client.get("/api/records/list")
    assert r.status_code == 200


def test_records_link(client):
    """记录关联 - Body 接收 JSON 数组"""
    # 先创建两条记录（通过 memo save）
    analysis = {"data_overview": {"距离": "5 km", "平均配速": "5'00\"/km"}, "performance_evaluation": {}, "improvement_suggestions": []}
    r1 = client.post("/api/memo/save", data={
        "memo_text": "A", "image_path": "/tmp/a.png", "analysis_result": json.dumps(analysis),
    })
    r2 = client.post("/api/memo/save", data={
        "memo_text": "B", "image_path": "/tmp/b.png", "analysis_result": json.dumps(analysis),
    })
    assert r1.status_code == 200 and r2.status_code == 200
    ids = [r1.json()["record_id"], r2.json()["record_id"]]
    # 发送 JSON 数组
    r = client.post("/api/records/link", json=ids)
    assert r.status_code == 200
    assert r.json()["linked_count"] == 2


# ---------- 数据统计 ----------
def test_stats_overview(client):
    """数据统计概览"""
    r = client.get("/api/stats/overview")
    assert r.status_code == 200


# ---------- qwen_service 响应解析 ----------
def test_run_score_daniels_formula():
    """跑步分数：Daniels-Gilbert 公式验证"""
    from app.services.run_score import compute_run_score, compute_vdot_raw

    # 5K 22分钟 -> VDOT 约 44-45
    data = {"distance_km": 5, "avg_pace": "4'24\"", "duration_hhmmss": "0:22:00"}
    vdot = compute_vdot_raw(data)
    assert vdot is not None
    assert 40 <= vdot <= 50

    # 10K 50分钟 -> 5分/km
    data2 = {"distance_km": 10, "avg_pace": "5'00\"", "duration_hhmmss": "0:50:00"}
    score = compute_run_score(data2)
    assert 0 <= score <= 100

    # 无配速返回 0
    assert compute_run_score({"distance_km": 10}) == 0


def test_extract_text_from_response():
    """测试 _extract_text_from_response 兼容 dict 与 object"""
    from app.services.qwen_service import _extract_text_from_response, _extract_text_from_content

    # dict 格式
    assert _extract_text_from_content({"text": "hello"}) == "hello"
    assert _extract_text_from_content({"image": "xxx"}) == ""

    # 模拟 response
    class MockResp:
        output = {
            "choices": [{
                "message": {
                    "content": [{"text": "json result"}]
                }
            }]
        }
    r = MagicMock()
    r.output = MockResp.output
    assert _extract_text_from_response(r) == "json result"


def test_analyze_strips_markdown_json(client, sample_image_bytes):
    """AI 返回 ```json ... ``` 包裹时能正确解析"""
    markdown_wrapped = '''```json
{"data_overview":{"距离":"14 km","平均配速":"5\'00\\"/km"},"performance_evaluation":{"整体评价":"表现良好"},"improvement_suggestions":["建议1"]}
```'''
    with patch("app.services.qwen_service.MultiModalConversation") as MockMM, \
         patch("app.services.qwen_service.image_to_base64", return_value="dummy"):
        resp = MagicMock()
        resp.status_code = 200
        MockMM.call.return_value = resp
        with patch("app.services.qwen_service._extract_text_from_response", return_value=markdown_wrapped):
            from app.services.qwen_service import analyze_coros_image
            result = analyze_coros_image("/tmp/x.png", "")
            assert "data_overview" in result
            assert result.get("performance_evaluation", {}).get("整体评价") == "表现良好"

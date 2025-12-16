from app.schemas.llm.architecture import ArchitectureLLMResponse
from app.schemas.llm.features import FeatureLLMResponse
from app.schemas.llm.quality import QualityLLMResponse
from app.schemas.llm.tech_stack import TechStackLLMResponse


def test_tech_stack_schema():
    data = {"items": [{"category": "backend", "name": "FastAPI"}]}
    parsed = TechStackLLMResponse.model_validate(data)
    assert parsed.items[0].name == "FastAPI"


def test_tech_stack_schema_ignores_non_numeric_requires():
    data = {"items": [{"category": "infra", "name": "Kubernetes", "requires": ["Docker", "123"]}]}
    parsed = TechStackLLMResponse.model_validate(data)
    assert parsed.items[0].requires == [123]


def test_feature_schema():
    data = {"features": [{"title": "Login", "description": "desc", "importance": 3, "feature_type": "must"}]}
    parsed = FeatureLLMResponse.model_validate(data)
    assert parsed.features[0].title == "Login"


def test_architecture_schema():
    data = {"components": [{"name": "API", "layer": "backend"}]}
    parsed = ArchitectureLLMResponse.model_validate(data)
    assert parsed.components[0].layer == "backend"


def test_architecture_schema_ignores_non_numeric_requires():
    data = {"components": [{"name": "API GW", "layer": "backend", "requires": ["API Gateway", "42"]}]}
    parsed = ArchitectureLLMResponse.model_validate(data)
    assert parsed.components[0].requires == [42]


def test_quality_schema():
    data = {
        "dod_items": [{"description": "Test", "category": "functional", "priority": 1}],
        "nfr_items": [{"type": "performance", "description": "fast"}],
        "risks": [{"description": "Risk", "impact": 2, "likelihood": 3}],
    }
    parsed = QualityLLMResponse.model_validate(data)
    assert parsed.dod_items[0].category == "functional"

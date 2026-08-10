import pytest
import asyncio
from app.agents.investigation.nodes.synthesize_evidence import synthesize_evidence
from app.agents.investigation.nodes.generate_hypotheses import generate_hypotheses
from app.agents.investigation.nodes.map_evidence import map_evidence
from app.agents.investigation.nodes.rank_hypotheses import rank_hypotheses

@pytest.mark.asyncio
async def test_rank_hypotheses():
    state = {
        "hypotheses": [
            {
                "temp_id": "h1",
                "title": "DB Issue",
                "category": "DATABASE",
                "description": "Database is down"
            },
            {
                "temp_id": "h2",
                "title": "App Issue",
                "category": "APPLICATION",
                "description": "Application memory leak"
            }
        ],
        "hypothesis_evidence_mappings": [
            {
                "hypothesis_temp_id": "h1",
                "evidence_id": "e1",
                "relationship": "SUPPORTS",
                "strength": "HIGH",
                "source_type": "LOG"
            },
            {
                "hypothesis_temp_id": "h1",
                "evidence_id": "e2",
                "relationship": "CONTRADICTS",
                "strength": "MEDIUM",
                "source_type": "CODE"
            },
            {
                "hypothesis_temp_id": "h2",
                "evidence_id": "e3",
                "relationship": "SUPPORTS",
                "strength": "MEDIUM",
                "source_type": "LOG"
            },
            {
                "hypothesis_temp_id": "h2",
                "evidence_id": "e4",
                "relationship": "SUPPORTS",
                "strength": "LOW",
                "source_type": "GIT_CHANGE"
            }
        ],
        "evidence": [
            {"id": "e1", "source_type": "LOG"},
            {"id": "e2", "source_type": "CODE"},
            {"id": "e3", "source_type": "LOG"},
            {"id": "e4", "source_type": "GIT_CHANGE"}
        ]
    }
    
    result = rank_hypotheses(state)
    hypotheses = result["hypotheses"]
    
    # h1 score: HIGH (+3) - MEDIUM (2) + diversity bonus (+1.0) = 2.0
    # h2 score: MEDIUM (+2) - 0 + diversity bonus (+0.5) = 2.5
    # So h2 should be ranked 1, h1 ranked 2.
    
    assert hypotheses[0]["temp_id"] == "h2"
    assert hypotheses[0]["rank"] == 1
    assert hypotheses[0]["preliminary_score"] == 35
    
    assert hypotheses[1]["temp_id"] == "h1"
    assert hypotheses[1]["rank"] == 2
    assert hypotheses[1]["preliminary_score"] == 10

"""Unit tests for the LangGraph-style routing logic. No DB/network needed."""
from graph.router import route_next


def base_state(**overrides) -> dict:
    state = {
        "query": "daily revenue monitor",
        "raw_data": None,
        "anomalies_found": None,
        "confidence_score": 0.0,
        "action_taken": None,
        "iteration_count": 0,
        "max_iterations": 8,
        "task_complete": False,
        "error": None,
    }
    state.update(overrides)
    return state


def test_routes_to_analytics_agent_first():
    assert route_next(base_state()) == "analytics_agent"


def test_routes_to_anomaly_agent_after_analytics():
    state = base_state(raw_data={"summary": {}})
    assert route_next(state) == "anomaly_agent"


def test_routes_to_action_agent_after_anomaly_detection():
    state = base_state(raw_data={"summary": {}}, anomalies_found=[])
    assert route_next(state) == "action_agent"


def test_routes_to_report_agent_when_complete():
    state = base_state(
        raw_data={"summary": {}},
        anomalies_found=[],
        action_taken="none",
    )
    assert route_next(state) == "report_agent"


def test_routes_to_report_agent_on_error():
    state = base_state(error="something broke")
    assert route_next(state) == "report_agent"


def test_routes_to_report_agent_when_task_complete_flag_set():
    state = base_state(task_complete=True)
    assert route_next(state) == "report_agent"


def test_routes_to_report_agent_when_max_iterations_reached():
    state = base_state(iteration_count=8, max_iterations=8)
    assert route_next(state) == "report_agent"

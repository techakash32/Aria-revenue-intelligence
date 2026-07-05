from typing import Optional, TypedDict


class AgentState(TypedDict):
    query: str
    raw_data: Optional[dict]
    anomalies_found: Optional[list]
    data_quality_issues: Optional[list]
    data_quality_has_critical: bool
    confidence_score: float
    action_taken: Optional[str]
    action_result: Optional[dict]
    iteration_count: int
    max_iterations: int
    task_complete: bool
    final_report: Optional[str]
    error: Optional[str]
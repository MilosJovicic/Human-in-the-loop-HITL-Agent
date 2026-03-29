from pydantic import BaseModel
from enum import Enum

class DefectReport(BaseModel):
    product_id: str
    defect_description: str
    production_line: str
    shift: str

class DefectAnalysis(BaseModel):
    severity: str
    defect_category: str
    affected_components: list[str]
    summary: str

class RootCauseResult(BaseModel):
    root_causes: list[str]
    contributing_factors: list[str]
    confidence: str # low, medium, high

class CorrectiveAction(BaseModel):
    action: str
    priority: str
    responsible_department: str

class ChainOutput(BaseModel):
    analysis: DefectAnalysis
    root_causes: RootCauseResult
    corrective_actions: list[CorrectiveAction]

# Human in the loop

class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    OVERRIDE = "override"

class EngineerReview(BaseModel):
    decision: ReviewDecision
    reviewer: str
    notes: str = ""
    override_severity: str | None = None # Only required if decision is OVERRIDE
    override_category: str | None = None # Only required if decision is OVERRIDE



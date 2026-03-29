from temporalio import activity
from temporalio.exceptions import ApplicationError
from openai import AuthenticationError, BadRequestError, PermissionDeniedError, NotFoundError
from models import DefectReport, DefectAnalysis, RootCauseResult, CorrectiveAction

NON_RETRYABLE_ERRORS = (AuthenticationError, PermissionDeniedError, BadRequestError, NotFoundError)


@activity.defn
async def analyze_defect(report: DefectReport) -> DefectAnalysis:
    from agents import analysis_agent

    activity.heartbeat("Starting defect analysis")
    prompt = (
        f"Product: {report.product_id}\n"
        f"Line: {report.production_line}\n"
        f"Shift: {report.shift}\n"
        f"Defect: {report.defect_description}"
    )
    try:
        result = await analysis_agent.run(prompt)
    except NON_RETRYABLE_ERRORS as e:
        raise ApplicationError(
            str(e), type="NonRetryableError", non_retryable=True,
        ) from e
    activity.logger.info(f"Analysis complete: severity={result.output.severity}")
    return result.output


@activity.defn
async def identify_root_causes(analysis: DefectAnalysis) -> RootCauseResult:
    from agents import root_cause_agent

    activity.heartbeat("Starting root cause identification")
    prompt = (
        f"Defect category: {analysis.defect_category}\n"
        f"Severity: {analysis.severity}\n"
        f"Affected components: {', '.join(analysis.affected_components)}\n"
        f"Summary: {analysis.summary}"
    )
    try:
        result = await root_cause_agent.run(prompt)
    except NON_RETRYABLE_ERRORS as e:
        raise ApplicationError(
            str(e), type="NonRetryableError", non_retryable=True,
        ) from e
    activity.logger.info(f"Root causes found: {len(result.output.root_causes)}")
    return result.output


@activity.defn
async def recommend_actions(analysis: DefectAnalysis, root_cause: RootCauseResult) -> list[CorrectiveAction]:
    from agents import action_agent

    activity.heartbeat("Starting corrective action recommendations")
    prompt = (
        f"Defect category: {analysis.defect_category}\n"
        f"Severity: {analysis.severity}\n"
        f"Affected components: {', '.join(analysis.affected_components)}\n"
        f"Summary: {analysis.summary}\n\n"
        f"Root causes: {', '.join(root_cause.root_causes)}\n"
        f"Contributing factors: {', '.join(root_cause.contributing_factors)}\n"
        f"Confidence: {root_cause.confidence}"
    )
    try:
        result = await action_agent.run(prompt)
    except NON_RETRYABLE_ERRORS as e:
        raise ApplicationError(
            str(e), type="NonRetryableError", non_retryable=True,
        ) from e
    activity.logger.info(f"Actions recommended: {len(result.output)}")
    return result.output
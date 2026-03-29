import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import (
        DefectReport,
        DefectAnalysis,
        RootCauseResult,
        CorrectiveAction,
        ChainOutput,
        EngineerReview,
        ReviewDecision,
    )
    from activities import analyze_defect, identify_root_causes, recommend_actions

LLM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)

REVIEW_TIMEOUT = timedelta(hours=24)


@workflow.defn
class DefectChainWorkflow:
    def __init__(self) -> None:
        self._awaiting_review = False
        self._review: EngineerReview | None = None

    @workflow.signal
    async def submit_review(self, review: EngineerReview) -> None:
        self._review = review
        self._awaiting_review = False

    @workflow.query
    def is_awaiting_review(self) -> bool:
        return self._awaiting_review

    @workflow.run
    async def run(self, report: DefectReport) -> ChainOutput:
        workflow.logger.info(f"Starting chain for product {report.product_id}")

        # Step 1: Analyze defect
        analysis: DefectAnalysis = await workflow.execute_activity(
            analyze_defect,
            report,
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=LLM_RETRY_POLICY,
        )

        # Human-in-the-loop: pause for engineer review if critical
        if analysis.severity == "critical":
            workflow.logger.info("Critical severity — pausing for engineer review")
            self._awaiting_review = True

            try:
                await workflow.wait_condition(
                    lambda: self._review is not None,
                    timeout=REVIEW_TIMEOUT,
                )
            except asyncio.TimeoutError:
                raise workflow.ApplicationError(
                    "Engineer review timed out after 24 hours"
                )

            review = self._review
            assert review is not None

            if review.decision == ReviewDecision.REJECT:
                raise workflow.ApplicationError(
                    f"Rejected by {review.reviewer}: {review.notes}"
                )

            if review.decision == ReviewDecision.OVERRIDE:
                workflow.logger.info(
                    f"Override by {review.reviewer}: "
                    f"severity={review.override_severity}, category={review.override_category}"
                )
                analysis = DefectAnalysis(
                    severity=review.override_severity or analysis.severity,
                    defect_category=review.override_category or analysis.defect_category,
                    affected_components=analysis.affected_components,
                    summary=analysis.summary,
                )

            workflow.logger.info(f"Review approved by {review.reviewer}, resuming chain")

        # Step 2: Identify root causes
        root_causes: RootCauseResult = await workflow.execute_activity(
            identify_root_causes,
            analysis,
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=LLM_RETRY_POLICY,
        )

        # Step 3: Recommend corrective actions
        actions: list[CorrectiveAction] = await workflow.execute_activity(
            recommend_actions,
            args=[analysis, root_causes],
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=LLM_RETRY_POLICY,
        )

        return ChainOutput(
            analysis=analysis,
            root_causes=root_causes,
            corrective_actions=actions,
        )

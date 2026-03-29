import asyncio
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from workflows import DefectChainWorkflow
from models import EngineerReview, ReviewDecision

WORKFLOW_ID = "defect-chain-PUMP-4421"  # Must match the ID used in starter.py


async def main():
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter,
    )
    handle = client.get_workflow_handle(WORKFLOW_ID)

    # Check if the workflow is actually waiting
    awaiting = await handle.query(DefectChainWorkflow.is_awaiting_review)
    if not awaiting:
        print("Workflow is not waiting for review. It may not be critical severity.")
        return

    print(f"Workflow {WORKFLOW_ID} is awaiting review.\n")
    print("Options:")
    print("  1. Approve (continue as-is)")
    print("  2. Override (change severity/category)")
    print("  3. Reject (cancel the chain)")

    choice = input("\nYour choice (1/2/3): ").strip()

    if choice == "1":
        review = EngineerReview(
            decision=ReviewDecision.APPROVE,
            reviewer="eng-marko",
            notes="Confirmed critical. Proceed with analysis.",
        )
    elif choice == "2":
        review = EngineerReview(
            decision=ReviewDecision.OVERRIDE,
            reviewer="eng-marko",
            notes="Downgrading after visual inspection.",
            override_severity="high",
        )
    elif choice == "3":
        review = EngineerReview(
            decision=ReviewDecision.REJECT,
            reviewer="eng-marko",
            notes="Duplicate report. Already tracked under PUMP-4419.",
        )
    else:
        print("Invalid choice.")
        return

    # Send the signal to the waiting workflow
    await handle.signal(DefectChainWorkflow.submit_review, review)
    print(f"\nReview sent: {review.decision.value}")


if __name__ == "__main__":
    asyncio.run(main())
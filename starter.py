import asyncio
import json

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from workflows import DefectChainWorkflow
from models import DefectReport

TASK_QUEUE = "prompt-chain-queue"


async def main():
    client = await Client.connect(
        "localhost:7233",
        data_converter=pydantic_data_converter,
    )

    report = DefectReport(
        product_id="PUMP-4421",
        defect_description=(
            "Hydraulic pump housing shows hairline cracks along the weld seam "
            "after 200 hours of operation. Leak detected during pressure test at 250 bar."
        ),
        production_line="Line-3",
        shift="Night",
    )

    print(f"Starting defect chain for {report.product_id}...")

    workflow_id = f"defect-chain-{report.product_id}"
    handle = await client.start_workflow(
        DefectChainWorkflow.run,
        report,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Workflow started: {workflow_id}")
    print("Waiting for result (workflow may pause if severity is critical)...")

    result = await handle.result()

    print("\n=== CHAIN RESULT ===\n")
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
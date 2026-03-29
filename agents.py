import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from models import DefectAnalysis, RootCauseResult, CorrectiveAction
from prompts import ANALYSIS_PROMPT, ROOT_CAUSE_PROMPT, CORRECTIVE_ACTION_PROMPT

load_dotenv()

# Disable client-level retries — let Temporal handle all retries
openai_client = AsyncOpenAI(
    max_retries=0,
    timeout=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
)

model = OpenAIModel(
    model_name=os.getenv("OPENAI_MODEL", "gpt-5.4-nano "),
    provider=OpenAIProvider(openai_client=openai_client),
)

# Step 1: Analyze the defect
analysis_agent = Agent(
    model=model,
    output_type=DefectAnalysis,
    system_prompt=ANALYSIS_PROMPT,
)

# Step 2: Identify root cause (receives the analysis as context)
root_cause_agent = Agent(
    model=model,
    output_type=RootCauseResult,
    system_prompt=ROOT_CAUSE_PROMPT,
)

# Step 3: Recommend corrective actions (receives analysis + root causes)
action_agent = Agent(
    model=model,
    output_type=list[CorrectiveAction],
    system_prompt=CORRECTIVE_ACTION_PROMPT,
)

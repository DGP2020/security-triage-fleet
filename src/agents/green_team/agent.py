import os
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
from src.schemas.ocsf import RemediationActivityEvent

def is_503_error(e):
    return isinstance(e, APIError) and (getattr(e, 'code', None) == 503 or "503" in str(e))

class GreenTeamFixer:
    def __init__(self):
        self.name = "green-team-fixer"
        # Load system prompt from green_team.md in the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        md_path = os.path.join(project_root, "green_team.md")
        with open(md_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
        
        self.client = genai.Client()

    @retry(
        wait=wait_exponential(min=2, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_503_error),
        reraise=True
    )
    async def invoke(self, prompt: str) -> str:
        """Executes Remediation Activity based on the provided JSON string containing the finding and JIT token."""
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                response_mime_type="application/json",
                response_schema=RemediationActivityEvent,
            ),
        )
        # Validate output against OCSF schema
        event_dict = json.loads(response.text)
        event = RemediationActivityEvent(**event_dict)
        return event.model_dump_json()

root_agent = GreenTeamFixer()

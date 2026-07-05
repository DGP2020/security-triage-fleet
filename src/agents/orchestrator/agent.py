import os
import json
from google import genai
from src.schemas.ocsf import NetworkActivityEvent, DetectionFindingEvent, RemediationActivityEvent
from src.agents.red_team.agent import RedTeamAttacker
from src.agents.blue_team.agent import BlueTeamDefender
from src.agents.green_team.agent import GreenTeamFixer

from google.adk.agents.base_agent import BaseAgent
from google.adk.events.event import Event
from google.genai.errors import APIError
from pydantic import PrivateAttr
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
from typing import AsyncGenerator

def is_503_error(e):
    return isinstance(e, APIError) and (getattr(e, 'code', None) == 503 or "503" in str(e))

class OrchestratorCoordinator(BaseAgent):
    name: str = "orchestrator-coordinator"
    description: str = "Event-driven coordinator for the simulation workflow."
    
    _system_prompt: str = PrivateAttr()
    _red_team: RedTeamAttacker = PrivateAttr()
    _blue_team: BlueTeamDefender = PrivateAttr()
    _green_team: GreenTeamFixer = PrivateAttr()

    def model_post_init(self, __context):
        super().model_post_init(__context)
        # Load system prompt from orchestrator.md in the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        md_path = os.path.join(project_root, "orchestrator.md")
        with open(md_path, "r", encoding="utf-8") as f:
            self._system_prompt = f.read()
        
        self._red_team = RedTeamAttacker()
        self._blue_team = BlueTeamDefender()
        self._green_team = GreenTeamFixer()

    @retry(
        wait=wait_exponential(min=2, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(is_503_error),
        reraise=True
    )
    async def invoke(self, prompt: str) -> str:
        """Runs the 3-phase A2A simulation based on the prompt (target context)."""
        
        simulation_report = {
            "simulation_id": "sim-uuid",
            "phases": {
                "attack": {"ocsf_event": {}, "attack_vector": ""},
                "evaluate": {"ocsf_finding": {}, "agent_trust_score": 1.0, "circuit_breaker_tripped": False},
                "remediate": {"vibe_diff": "", "hitl_approved": False, "quarantine_status": "", "refactored_code": ""}
            },
            "jit_tokens_issued": [],
            "simulation_outcome": "DETECTED"
        }
        
        # Phase 1: Attack (Red Team)
        red_output = await self._red_team.invoke(prompt)
        # Validate and store
        red_event = NetworkActivityEvent.model_validate_json(red_output)
        simulation_report["phases"]["attack"]["ocsf_event"] = red_event.model_dump()
        
        if red_event.unmapped:
            simulation_report["phases"]["attack"]["attack_vector"] = red_event.unmapped.attack_vector

        # Phase 2: Evaluate (Blue Team)
        blue_output = await self._blue_team.invoke(red_output)
        # Validate and store
        blue_finding = DetectionFindingEvent.model_validate_json(blue_output)
        simulation_report["phases"]["evaluate"]["ocsf_finding"] = blue_finding.model_dump()
        
        trust_score = 1.0
        violations = 0
        if blue_finding.unmapped:
            aba = blue_finding.unmapped.aba_check_results
            violations = sum([
                aba.agbom_violation,
                aba.execution_loop_detected,
                aba.prompt_injection_detected,
                aba.semantic_drift_detected,
            ])
            trust_score = round(max(0.0, 1.0 - violations * 0.3), 1)
            circuit_breaker = violations > 0
            simulation_report["phases"]["evaluate"]["agent_trust_score"] = trust_score
            simulation_report["phases"]["evaluate"]["circuit_breaker_tripped"] = circuit_breaker
        
        if violations > 0:
            try:
                vibe_diff_prompt = (
                    f"System: {self._system_prompt}\n"
                    f"Translate this Detection Finding into a plain-English Vibe Diff.\n"
                    f"List exactly three bullet sections:\n"
                    f"1. Revoke: what tool/access will be revoked and why\n"
                    f"2. Refactor: what code will be hardened and how\n"
                    f"3. Unchanged: what will NOT be changed\n"
                    f"Use backticks for code/tool names.\n\n"
                    f"Detection Finding:\n{blue_output}"
                )
                client = genai.Client()
                vibe_diff_response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=vibe_diff_prompt
                )
                vibe_diff_text = vibe_diff_response.text or "Vibe diff generation returned empty response."
            except Exception as vd_err:
                vibe_diff_text = f"Vibe diff generation failed: {vd_err}"

            simulation_report["phases"]["remediate"]["vibe_diff"] = vibe_diff_text
            simulation_report["simulation_outcome"] = "PENDING_HITL"
            
            # Simulated HITL approval handling for the playground demo
            if "approve" in prompt.lower():
                jit_token = {"id": "jit-1234", "expires_at": "2030-01-01T00:00:00Z", "allowed_actions": ["stateful_quarantine", "auto_refactoring"]}
                simulation_report["jit_tokens_issued"].append(jit_token)
                
                # Combine finding and token to send to green team
                green_input = json.dumps({
                    "finding": blue_finding.model_dump(),
                    "jit_token": jit_token
                })
                
                green_output = await self._green_team.invoke(green_input)
                green_event = RemediationActivityEvent.model_validate_json(green_output)
                
                if green_event.unmapped:
                    simulation_report["phases"]["remediate"]["quarantine_status"] = green_event.unmapped.quarantine_status
                    simulation_report["phases"]["remediate"]["refactored_code"] = green_event.unmapped.refactored_code
                    simulation_report["simulation_outcome"] = "REMEDIATED"

        return json.dumps(simulation_report, indent=2)

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        # Extract prompt from user_content or events
        prompt = ""
        if ctx.user_content and ctx.user_content.parts:
            prompt = "".join(part.text for part in ctx.user_content.parts if part.text)
        else:
            events = ctx._get_events(current_invocation=True)
            for event in reversed(events):
                if event.author == "user" and event.content and event.content.parts:
                    prompt = "".join(part.text for part in event.content.parts if part.text)
                    break

        response_str = await self.invoke(prompt)

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            message=response_str
        )

root_agent = OrchestratorCoordinator()

from __future__ import annotations
from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, Field
from uuid import uuid4


Preset = Literal["ai-agent", "life-automation", "knowledge-work", "custom"]
JTBDFrame = Literal["forces", "fse", "outcomes", "job-story"]
DepthMode = Literal["sprint", "standard", "deep"]
StyleMode = Literal["socratic", "scenario-first", "metaphor-first", "form"]
Language = Literal["en", "ru"]


class InterviewMode(BaseModel):
    depth: DepthMode = "standard"
    style: StyleMode = "scenario-first"


class Meta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created: datetime = Field(default_factory=datetime.utcnow)
    preset: Preset = "custom"
    jtbd_frame: JTBDFrame = "job-story"
    interview_mode: InterviewMode = Field(default_factory=InterviewMode)
    language: Language = "en"


class Problem(BaseModel):
    what_hurts: str = ""
    cost_today: str = ""


class Needs(BaseModel):
    functional: list[str] = Field(default_factory=list)
    emotional: list[str] = Field(default_factory=list)
    social: list[str] = Field(default_factory=list)


class JTBD(BaseModel):
    situation: str = ""
    motivation: str = ""
    outcome: str = ""


class BeforeAfter(BaseModel):
    before_external: str = ""
    before_internal: str = ""
    after_external: str = ""
    after_internal: str = ""


class Scenario(BaseModel):
    title: str
    vignette: str


class Trigger(BaseModel):
    type: Literal["manual", "scheduled", "event"] = "manual"
    detail: str = ""


class ConceptImagery(BaseModel):
    metaphor: str = ""
    visual_style: str = ""
    nano_banana_prompt: str = ""


class CoverageEntry(BaseModel):
    confidence: float = 0.0
    inferred: bool = False
    turns_spent: int = 0


class TranscriptTurn(BaseModel):
    role: Literal["assistant", "user"]
    text: str
    ts: datetime = Field(default_factory=datetime.utcnow)


class InterviewState(BaseModel):
    phase: str = "opening"  # Phase value
    current_subject_key: str | None = None
    subjects_landed: list[str] = Field(default_factory=list)
    follow_ups_on_current: int = 0
    max_follow_ups: int = 2
    asked_questions_per_phase: dict[str, list[str]] = Field(default_factory=dict)


class DesignJSON(BaseModel):
    meta: Meta
    hook: str = ""
    problem: Problem = Field(default_factory=Problem)
    needs: Needs = Field(default_factory=Needs)
    jtbd: JTBD = Field(default_factory=JTBD)
    jtbd_frame_extension: dict[str, Any] = Field(default_factory=dict)
    before_after: BeforeAfter = Field(default_factory=BeforeAfter)
    scenarios: list[Scenario] = Field(default_factory=list)
    cta: str = ""
    trigger: Trigger = Field(default_factory=Trigger)
    inputs: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    concept_imagery: ConceptImagery = Field(default_factory=ConceptImagery)
    coverage: dict[str, CoverageEntry] = Field(default_factory=dict)
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    interview_state: InterviewState = Field(default_factory=InterviewState)

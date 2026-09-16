from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, max_length=6000)]
Framework = Literal['RBM', 'GMM', 'CPM', 'RSM', 'Legitimacy_Layer', 'History_Analysis', 'Value_Formation']

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Context(Model):
    representation: Literal['verbatim', 'summary', 'unknown'] = 'unknown'
    response_status: Literal['answered', 'unknown', 'context_dependent', 'not_applicable', 'declined'] | None = None
    omitted_information: str | None = Field(default=None, max_length=1000)
    speaker: Literal['human', 'ai', 'source']
    text: Text

class AlignRequest(Model):
    input_message: Text
    ai_interpretation: Text | None = None
    context: list[Context] = Field(default_factory=list, max_length=12)
    language: Literal['ja', 'en'] = 'ja'
    frameworks: list[Framework] | None = Field(default=None, max_length=3)

    @model_validator(mode='after')
    def limits(self):
        if not self.input_message.strip():
            raise ValueError('input_message must not be blank')
        if len(self.model_dump_json()) > 24000:
            raise ValueError('combined request is too large')
        return self

class Evidence(Model):
    source: str = Field(min_length=1, max_length=60)
    quote: Text

class Intake(Model):
    kind: Literal['handshake', 'unclear', 'context_insufficient', 'substantive']
    evidence: list[Evidence] = Field(max_length=16)
    frameworks: list[Framework] = Field(max_length=3)

class Premise(Model):
    statement: Text
    source: Literal['user_explicit', 'user_implied', 'provided_source', 'agent_inference']
    status: Literal['explicit', 'inferred', 'unclear']
    support_state: Literal['provided', 'unsupported', 'disputed', 'unknown', 'not_applicable']
    materiality: Literal['low', 'medium', 'high']
    execution_effect: Text
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    externally_verified: Literal[False] = False

class Hypothesis(Model):
    blocks_execution: bool = True
    interpretation: Text
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    verification_question: Text

class Gap(Model):
    blocks_execution: bool = True
    human_premise: Text | None
    ai_premise: Text | None
    difference: Text
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    verification_question: Text

class View(Model):
    premises: list[Premise] = Field(default_factory=list, max_length=16)
    understanding: Text
    hypotheses: list[Hypothesis] = Field(max_length=8)
    premise_gaps: list[Gap] = Field(max_length=8)
    unknowns: list[Text] = Field(max_length=12)
    questions: list[Text] = Field(max_length=8)

class Draft(Model):
    fact: list[Premise] = Field(max_length=16)
    view: View
    care: list[Premise] | None = Field(max_length=16)

class Fact(Model):
    kind: Literal['observed_text'] = 'observed_text'
    source: str
    quote: str
    externally_verified: Literal[False] = False

class Meta(Model):
    observation_scope: Literal['submitted_material_only'] = 'submitted_material_only'
    profile: Literal['workflow-premise-map-v0.1'] = 'workflow-premise-map-v0.1'
    frameworks_used: list[Framework]
    comparison: Literal['provided_ai_interpretation', 'engine_hypothesis', 'not_applicable']
    delta_v: None = None
    execution_authorized: Literal[False] = False
    knowledge_sha256: str

class AlignResponse(Model):
    schema_version: Literal['0.1.0'] = '0.1.0'
    request_id: str
    status: Literal['handshake', 'unknown', 'context_insufficient', 'needs_clarification', 'mapped', 'mapped_with_divergence']
    observations: list[Fact]
    fact: list[Premise]
    view: View
    care: list[Premise] | None
    acknowledgment: str | None = None
    meta: Meta

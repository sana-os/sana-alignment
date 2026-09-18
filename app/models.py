from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Text = Annotated[str, StringConstraints(min_length=1, max_length=6000)]
LanguageTag = Annotated[str, StringConstraints(min_length=2, max_length=35, pattern=r'^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$')]
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
    language: LanguageTag = Field(default='en', description='Requested language for generated prose. Quotes stay verbatim. Common language/script/region tags, not full BCP 47 registry validation.')
    frameworks: Annotated[list[Framework], Field(max_length=3)] | Literal['auto'] | None = Field(default_factory=list, description='No detailed lens by default. Use auto (or legacy null) for selection, or a list for explicit lenses.')

    @field_validator('language')
    @classmethod
    def normalize_language(cls, value):
        parts = value.split('-')
        return '-'.join([parts[0].lower()] + [
            x.title() if len(x) == 4 and x.isalpha() else
            x.upper() if len(x) == 2 and x.isalpha() else x.lower()
            for x in parts[1:]
        ])

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

class Extraction(Model):
    kind: Literal['handshake', 'unclear', 'context_insufficient', 'substantive'] = Field(description='Hint about interpretable premises, not readiness to execute the task. A missing document body does not prevent comparing an explicit transfer boundary with an AI proposal. Pure greetings alone are handshake, not Care.')
    evidence: list[Evidence] = Field(max_length=32, description='Extract explicit statements as verbatim clauses: goals, boundaries, claims and supplied interpretations. Keep human and AI sources separate. Do not classify Fact/View/Care, infer motives, or solve the task. Preserve each known statement even if another part is unclear.')
    frameworks: list[Framework] = Field(max_length=3)

class PremiseFields(Model):
    statement: Text
    source: Literal['user_explicit', 'user_implied', 'provided_source', 'agent_inference']
    status: Literal['explicit', 'inferred', 'unclear'] = Field(description='Explicit means stated by the attributed source. user_explicit requires explicit; user_implied and agent_inference require inferred or unclear.')
    support_state: Literal['provided', 'unsupported', 'disputed', 'unknown', 'not_applicable']
    materiality: Literal['low', 'medium', 'high']
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    externally_verified: Literal[False] = False

class Premise(PremiseFields):
    execution_effect: Text = Field(description='Consequence of this attributed premise, not a new requirement. Keep implementation details from an AI proposal on the AI proposal; never attach them to a human goal unless the human supplied them. Do not add an unstated motive, legal/privacy rationale, or guarantee of compliance/safety.')

class CareDraft(PremiseFields):
    """What matters in the task, with attribution; no execution-effect generation."""
    support_state: Literal['not_applicable'] = Field(description='Always not_applicable for a goal, value, priority, or constraint. Evidence records who stated it, not proof of a value.')

class CarePremise(CareDraft):
    execution_effect: None = Field(default=None, description='Not assessed for Care. The server supplies null; consult the stated concern and View for premise differences, not an invented implementation plan.')

class Hypothesis(Model):
    blocks_execution: bool = True
    interpretation: Text
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    verification_question: Text | None = Field(default=None, description='Null when no new information is needed. Never ask permission to relax an explicit constraint.')

class Gap(Model):
    kind: Literal['constraint_conflict', 'interpretation_difference', 'missing_premise'] = Field(default='interpretation_difference', description='A comparison between the human position and supplied AI proposal, not a list of later implementation needs. missing_premise needs a stated position on at least one side.')
    blocks_execution: bool = Field(default=True, description='A known conflict or material unresolved alignment issue. Missing later implementation inputs alone do not create a premise gap or a blocking signal here.')
    human_premise: Text | None = Field(description='Human position relevant to this comparison, or null if not stated. Do not import the AI implementation into it. Both sides cannot be null or blank.')
    ai_premise: Text | None = Field(description='Position in the supplied AI proposal, or null if not stated. Do not invent a replacement proposal to fill this field. Both sides cannot be null or blank.')
    difference: Text = Field(description='Explain the supported comparison. Do not list unspecified implementation options, invent candidate answers, or treat a missing alternative method as a new requirement.')
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    verification_question: Text | None = Field(default=None, description='Null when no new information is needed. Never ask permission to relax an explicit constraint.')

class UnresolvedPremise(Model):
    statement: Text = Field(description='One missing or unclear variable, without invented possible answers or replacement requirements.')
    scope: Literal['alignment', 'execution'] = Field(description='alignment only if the missing information changes interpretation or premise comparison; execution for later implementation. Missing document content is execution-only when a transfer conflict is already identifiable.')
    evidence: list[Evidence] = Field(default_factory=list, max_length=8, description='Supporting text anchors if available; absent information itself cannot be quoted.')
    question: Text | None = Field(default=None, description='A focused comparison question, or null. Execution-only issues and already declined/unknown answers must not cause questions here.')

class MappingView(Model):
    premises: list[Premise] = Field(default_factory=list, max_length=16, description='Interpretations, proposals and framings, with their own attribution. Plain user goals and prohibitions belong in Care; do not repeat them here to attach an AI implementation. Human evaluations or framings can still belong in View. An AI proposal is provided_source, not a user instruction or verified fact.')
    understanding: Text
    hypotheses: list[Hypothesis] = Field(max_length=8, description='Engine interpretation hypotheses only when no ai_interpretation was supplied. With a supplied AI proposal this must be empty; use premise_gaps and unresolved for comparison and genuine unknowns. Never use this field to prescribe an unstated replacement plan.')
    premise_gaps: list[Gap] = Field(max_length=8)
    unresolved: list[UnresolvedPremise] = Field(max_length=12, description='Preserve uncertainty locally. Do not erase known goals/constraints or demand implementation details to finish an already determined comparison. Empty is valid.')

class View(MappingView):
    unresolved: list[UnresolvedPremise] = Field(default_factory=list, max_length=12)
    unknowns: list[Text] = Field(max_length=12, description='Alignment-scope unresolved statements, derived by the server.')
    questions: list[Text] = Field(max_length=1, description='At most one alignment question, derived by the server. Execution-only details never create a question here.')

class Draft(Model):
    kind: Literal['mapped', 'unclear', 'context_insufficient'] = Field(description='mapped when any task premises can be classified/compared, even with local unknowns. Other kinds describe broad interpretation limits, not missing execution inputs. Known portions are still retained.')
    fact: list[Premise] = Field(max_length=16, description='Factual claims about the task. Exclude instructions, goals, preferences, and prohibitions: those belong in Care. Observations already record what was uttered. Empty is valid.')
    view: MappingView
    care: list[CareDraft] | None = Field(max_length=16, description='Stated goals, values, priorities and boundaries, with their attribution. A pure greeting belongs to handshake, not Care. Do not invent empathy, motives or replacement methods. Null if what matters cannot be identified.')

class Fact(Model):
    kind: Literal['observed_text'] = 'observed_text'
    source: str
    quote: str
    externally_verified: Literal[False] = False

class Meta(Model):
    requested_language: str
    short_reply_language: str | None = None
    language_fallback: bool = False
    observation_scope: Literal['submitted_material_only'] = 'submitted_material_only'
    profile: Literal['workflow-premise-map-v0.4'] = 'workflow-premise-map-v0.4'
    stages_completed: list[Literal['extraction', 'mapping']] = Field(default_factory=list)
    frameworks_used: list[Framework]
    comparison: Literal['provided_ai_interpretation', 'engine_hypothesis', 'not_applicable']
    delta_v: None = None
    execution_authorized: Literal[False] = False
    knowledge_sha256: str

class AlignResponse(Model):
    schema_version: Literal['0.4.0'] = '0.4.0'
    request_id: str
    status: Literal['handshake', 'unknown', 'context_insufficient', 'revision_required', 'needs_clarification', 'mapped', 'mapped_with_divergence']
    observations: list[Fact]
    fact: list[Premise]
    view: View
    care: list[CarePremise] | None
    acknowledgment: str | None = None
    meta: Meta

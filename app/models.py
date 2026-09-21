from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Text = Annotated[str, StringConstraints(min_length=1, max_length=6000)]
MAX_EXTRACTION_REFERENCES = 256
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
    processing_mode: Literal['low', 'medium', 'high'] | None = Field(default=None,
        description='Processing allowance, not an accuracy score. low: no mapping correction; medium: at most one; high: at most two. Omitted uses server configuration. All modes retain the same validation and total deadline.')
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

class ExtractedEvidence(Evidence):
    function: Literal['state', 'request', 'concern', 'proposal', 'unknown', 'mixed', 'assumption', 'other', 'unclear'] = Field(default='unclear', description='Communicative function of this exact clause, not a Fact/View/Care verdict. state: condition/capability/event reported as actually holding, not merely posited as a plan prerequisite; this does not require external verification; request: an explicit instruction asking for an action or outcome, including an adopted method; concern: a stated goal, preference, priority, requirement or prohibition; proposal: a tentative option or supplied AI plan, not an adopted human instruction; unknown: an explicitly unspecified variable or open topic, including fragments in an Unknowns section, NOT an expressed priority; mixed: a clause combining factual state with a requirement or other role that cannot be separated safely; assumption: a capability or condition explicitly posited for a plan, including declarative prerequisites framed by Assumptions; use literal context, not a heading-only rule; actual reported test results remain state, and combined reports/assumptions are mixed; other: neither; unclear: function uncertain. Human "Display fictional records" and "架空の情報を表示してください" are request, not proposal. A polite request is still a request. "The PC is not connected" is state; "Do not connect the PC" is concern. Practical implications do not change state into request/concern. Split mixed clauses and preserve speaker, negation and modality.')

class Extraction(Model):
    kind: Literal['handshake', 'unclear', 'context_insufficient', 'substantive'] = Field(description='Hint about interpretable premises, not readiness to execute the task. A missing document body does not prevent comparing an explicit transfer boundary with an AI proposal. Pure greetings alone are handshake, not Care.')
    evidence: list[ExtractedEvidence] = Field(max_length=MAX_EXTRACTION_REFERENCES, description='Select relevant verbatim clauses and label their communicative function, within the shared reference budget. Do not repeat references or pad the list to its limit. Keep human and AI sources separate. Do not perform full Fact/View/Care mapping, infer motives, or solve the task. Preserve each known statement even if another part is unclear. Exact clauses labelled request or concern are eligible as Care anchors. Do not drop a requested outcome merely because the same input also contains a prohibition.')
    frameworks: list[Framework] = Field(max_length=3)

class PremiseFields(Model):
    statement: Text
    source: Literal['user_explicit', 'user_implied', 'provided_source', 'agent_inference']
    status: Literal['explicit', 'inferred', 'unclear'] = Field(description='Explicit means stated by the attributed source. user_explicit requires explicit; user_implied and agent_inference require inferred or unclear.')
    support_state: Literal['provided', 'unsupported', 'disputed', 'unknown', 'not_applicable'] = Field(description='Support for this statement at its stated scope within submitted material, not external truth. provided: cited material supplies a basis, including faithful attributed reports of plans/assumptions; unsupported: assertion exceeds supplied support; disputed: submitted material explicitly contests it; unknown: support/truth of the assessed proposition is undetermined; not_applicable: goal/value/requirement represented as such. Reporting a plan assumption is not establishing its truth. Do not assign unsupported merely because the source is AI or externally_verified is false.')
    materiality: Literal['low', 'medium', 'high']
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    externally_verified: Literal[False] = False

class Premise(PremiseFields):
    execution_effect: Text | None = Field(default=None, description='Null unless an intended effect is explicitly quoted in this premise evidence. A non-null value is the exact cited source quote, not a generated prediction, verified consequence or completed action. Its original language is preserved.')

class CareDraft(PremiseFields):
    """What matters in the task, with attribution; no execution-effect generation."""
    support_state: Literal['not_applicable'] = Field(description='Always not_applicable for a goal, value, priority, or constraint. Evidence records who stated it, not proof of a value.')
    statement: Text = Field(description='An exact original clause expressing a requested outcome, goal, preference, priority or boundary, selected from extraction request/concern anchors and cited in this item evidence. Never convert a reported condition into a directive, even under an inferred label. Original language is preserved. Practical implications belong in View with tentative attribution, if relevant, not invented Care.')

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
    human_premise: Text | None = Field(description='Exact cited human position selected for this comparison, or null if not stated. A description of what the human did not specify is not a stated position. Both sides cannot be null or blank.')
    ai_premise: Text | None = Field(description='Exact cited position in the supplied AI proposal, or null if not stated. Includes the selected clause qualifications and alternatives. Both sides cannot be null or blank.')
    difference: str = Field(min_length=1, max_length=14000, description='Server-rendered comparison kind and exact source-labelled positions, preserving alternatives and qualifications. A null side means no position was selected from submitted material, not proof of absence elsewhere. This is an extractive comparison, not a free-form explanation or independently verified conclusion.')
    evidence: list[Evidence] = Field(min_length=1, max_length=8)
    verification_question: Text | None = Field(default=None, description='Null when no new information is needed. Never ask permission to relax an explicit constraint.')

class UnresolvedPremise(Model):
    statement: Text = Field(description='One missing or unclear variable, without invented possible answers or replacement requirements.')
    scope: Literal['alignment', 'execution'] = Field(description='alignment only if the missing information changes interpretation or premise comparison; execution for later implementation. Missing document content is execution-only when a transfer conflict is already identifiable.')
    evidence: list[Evidence] = Field(default_factory=list, max_length=8, description='Supporting text anchors if available; absent information itself cannot be quoted.')
    question: Text | None = Field(default=None, description='A focused comparison question, or null. Execution-only issues and already declined/unknown answers must not cause questions here.')

class SummaryDraft(Model):
    evidence: list[Evidence] = Field(default_factory=list, max_length=3, description='Select up to three source quotations for an extractive overview, preferably one human and one supplied-AI quote. Do not write a summary or add actions. Empty selects the full submitted input and AI proposal as a server fallback. The server supplements a missing input_message or ai_interpretation source with that full original source.')

class MappingView(Model):
    premises: list[Premise] = Field(default_factory=list, max_length=16, description='Interpretations, proposals and framings, with their own attribution. Plain user goals and prohibitions belong in Care; do not repeat them here to attach an AI implementation. Human evaluations or framings can still belong in View. An AI proposal is provided_source, not a user instruction or verified fact.')
    understanding: SummaryDraft = Field(description='Source selection only; the server renders attributed original quotations. No free-form prose.')
    hypotheses: list[Hypothesis] = Field(max_length=8, description='Engine interpretation hypotheses only when no ai_interpretation was supplied. With a supplied AI proposal this must be empty; use premise_gaps and unresolved for comparison and genuine unknowns. Never use this field to prescribe an unstated replacement plan.')
    premise_gaps: list[Gap] = Field(max_length=8)
    unresolved: list[UnresolvedPremise] = Field(max_length=12, description='Preserve uncertainty locally. Do not erase known goals/constraints or demand implementation details to finish an already determined comparison. Empty is valid.')

class View(MappingView):
    understanding: str = Field(min_length=1, max_length=32000, description='Source-labelled original excerpts for mapped results, or a localized short reply for greeting/uninterpretable input. Not a newly authored interpretation. Consult premises, gaps and unresolved for analysis.')
    understanding_evidence: list[Evidence] = Field(default_factory=list, max_length=5, description='Exact excerpts rendered in understanding; empty for localized short replies.')
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
    profile: Literal['workflow-premise-map-v0.5'] = 'workflow-premise-map-v0.5'
    understanding_mode: Literal['source_excerpts', 'short_reply'] = 'source_excerpts'
    stages_completed: list[Literal['extraction', 'mapping']] = Field(default_factory=list)
    frameworks_used: list[Framework]
    comparison: Literal['provided_ai_interpretation', 'engine_hypothesis', 'not_applicable']
    delta_v: None = None
    execution_authorized: Literal[False] = False
    knowledge_sha256: str

class AlignResponse(Model):
    schema_version: Literal['0.5.0'] = '0.5.0'
    request_id: str
    status: Literal['handshake', 'unknown', 'context_insufficient', 'revision_required', 'needs_clarification', 'mapped', 'mapped_with_divergence']
    observations: list[Fact]
    fact: list[Premise]
    view: View
    care: list[CarePremise] | None
    acknowledgment: str | None = None
    meta: Meta

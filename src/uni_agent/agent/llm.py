"""Model client abstraction.

The graph depends on the :class:`ModelClient` protocol, never on a concrete
provider. This keeps the agent provider-agnostic and -- crucially -- lets tests
inject a deterministic :class:`ScriptedModelClient` so no live LLM is required.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from uni_agent.agent import prompts
from uni_agent.agent.contracts import AnswerDraft, QuestionAnalysis, SQLCandidate
from uni_agent.db.adapter import QueryResult


@runtime_checkable
class ModelClient(Protocol):
    """Every LLM interaction the agent needs, as typed structured calls."""

    def analyze_question(
        self, question: str, schema_context: str, dialect: str
    ) -> QuestionAnalysis: ...

    def generate_sql(
        self, question: str, schema_context: str, dialect: str, analysis: QuestionAnalysis
    ) -> SQLCandidate: ...

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str,
        failed_sql: str,
        errors: list[str],
        attempt: int,
    ) -> SQLCandidate: ...

    def synthesize_answer(self, question: str, sql: str, result: QueryResult) -> AnswerDraft: ...


def _render_rows(result: QueryResult, sample: int = 50) -> str:
    records = result.as_records()[:sample]
    if not records:
        return "(no rows)"
    return "\n".join(str(record) for record in records)


class OpenAIModelClient:
    """Concrete client using LangChain's OpenAI chat model with structured output.

    Imported lazily so the package (and tests) work without langchain-openai or
    an API key installed.
    """

    def __init__(self, *, model: str, api_key: str | None = None, temperature: float = 0.0):
        from langchain_openai import ChatOpenAI

        self._llm = ChatOpenAI(model=model, api_key=api_key, temperature=temperature)  # type: ignore[arg-type]

    def _structured(self, schema, system: str, user: str):
        from langchain_core.messages import HumanMessage, SystemMessage

        runnable = self._llm.with_structured_output(schema)
        return runnable.invoke([SystemMessage(content=system), HumanMessage(content=user)])

    def analyze_question(
        self, question: str, schema_context: str, dialect: str
    ) -> QuestionAnalysis:
        return self._structured(
            QuestionAnalysis,
            prompts.ANALYZE_SYSTEM,
            prompts.ANALYZE_USER.format(schema_context=schema_context, question=question),
        )

    def generate_sql(
        self, question: str, schema_context: str, dialect: str, analysis: QuestionAnalysis
    ) -> SQLCandidate:
        return self._structured(
            SQLCandidate,
            prompts.GENERATE_SYSTEM,
            prompts.GENERATE_USER.format(
                dialect=dialect,
                schema_context=schema_context,
                question=question,
                intent=analysis.intent,
            ),
        )

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        dialect: str,
        failed_sql: str,
        errors: list[str],
        attempt: int,
    ) -> SQLCandidate:
        return self._structured(
            SQLCandidate,
            prompts.REPAIR_SYSTEM,
            prompts.REPAIR_USER.format(
                dialect=dialect,
                schema_context=schema_context,
                question=question,
                failed_sql=failed_sql,
                errors="; ".join(errors) or "unknown error",
                attempt=attempt,
            ),
        )

    def synthesize_answer(self, question: str, sql: str, result: QueryResult) -> AnswerDraft:
        return self._structured(
            AnswerDraft,
            prompts.ANSWER_SYSTEM,
            prompts.ANSWER_USER.format(
                question=question,
                sql=sql,
                columns=", ".join(result.columns) or "(none)",
                rows=_render_rows(result),
            ),
        )

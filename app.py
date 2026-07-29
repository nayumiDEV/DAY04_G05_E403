"""Streamlit UI for the Day04 research agent.

Reuses `run_model_tool_loop` from chat.py so behavior stays in sync with the
CLI. Each user message is dispatched through the same code path; rounds and
tool_events are surfaced verbatim so demos can show the full trace.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import (
    assistant_tool_message,
    execute_tool_call,
    json_text,
    tool_results_message,
    trim_history,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def _provider_safe(provider_name: str, model: str | None):
    """Instantiate provider; surface clear error if API key missing."""
    try:
        provider = make_provider(provider_name)
        if model:
            provider.default_model = model
        return provider, None
    except Exception as exc:  # missing API key, network, etc.
        return None, f"{type(exc).__name__}: {exc}"


def _render_round(round_record: dict, idx: int) -> None:
    with st.expander(f"Round {idx} — {len(round_record.get('tool_calls', []))} tool call(s)", expanded=False):
        if round_record.get("assistant_text"):
            st.markdown("**Assistant text:**")
            st.markdown(f"> {round_record['assistant_text']}")
        st.markdown("**Tool calls:**")
        for call in round_record.get("tool_calls", []):
            st.code(f"{call['name']}({json.dumps(call['args'], ensure_ascii=False, sort_keys=True)})", language="json")
        st.markdown("**Tool results:**")
        for event in round_record.get("tool_results", []):
            result = event.get("result", {})
            status = "OK" if "error" not in result else "ERROR"
            st.markdown(f"- `{event['tool']}` → **{status}**")
            st.code(json_text(result, max_chars=1200), language="json")


def run_one_turn(
    *,
    provider,
    messages: list[dict],
    openai_tools: list[dict],
    model: str | None,
    max_tool_rounds: int,
) -> dict:
    """Mirror chat.run_model_tool_loop but stream rounds back to Streamlit."""
    working_messages = list(messages)
    rounds: list[dict] = []
    all_tool_events: list[dict] = []

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(working_messages, openai_tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in calls],
            "tool_results": [],
        }
        if not calls:
            rounds.append(round_record)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict] = []
        awaiting = False
        asked_question = None
        for call in calls:
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)
            result = event.get("result", {}) or {}
            if isinstance(result, dict) and result.get("awaiting_user"):
                awaiting = True
                asked_question = result.get("question") or call.args.get("question")
            else:
                non_clarification_events.append(event)

        rounds.append(round_record)
        if awaiting:
            return {
                "status": "waiting_for_user",
                "assistant_text": asked_question or "Bạn bổ sung thêm thông tin nhé.",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(tool_results_message(non_clarification_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds. Inspect transcript for details.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


def save_transcript(version: str, provider_name: str, transcript: dict) -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    safe_version = version.replace("/", "_")
    path = TRANSCRIPTS_DIR / f"{safe_version}_{provider_name}_{timestamp}.transcript.json"
    transcript["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def main() -> None:
    st.set_page_config(page_title="Day04 Research Agent", layout="wide")
    st.title("🔬 Day04 Research Agent — UI")
    st.caption("Routes to real tools (timeline, lookup, social_search, trending_topics, …) and shows the full trace.")

    with st.sidebar:
        st.header("Configuration")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
        version = st.text_input("Artifact version (v0 / v1 / v2 / v3)", value="v3")
        model_override = st.text_input("Model (optional override)", value="")
        max_rounds = st.slider("Max tool rounds per turn", 1, 8, 4)
        st.divider()
        st.markdown("**Status:**")
        if "provider" not in st.session_state or st.session_state.get("provider_name") != provider_name:
            provider, err = _provider_safe(provider_name, model_override or None)
            st.session_state.provider = provider
            st.session_state.provider_error = err
            st.session_state.provider_name = provider_name
        if st.session_state.get("provider_error"):
            st.error(f"Provider init failed: {st.session_state.provider_error}")
        else:
            st.success(f"Provider ready: {provider_name}")

    if st.session_state.get("provider_error"):
        st.warning("Fix provider init error in the sidebar to start chatting.")
        return

    provider = st.session_state.provider
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(declarations)
    artifact_version = build_artifact_version(version, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")

    st.markdown(
        f"`artifact_version` = **{artifact_version.artifact_version}** "
        f"(prompt `{artifact_version.prompt_hash[:8]}`, tools `{artifact_version.tools_hash[:8]}`) · "
        f"`{len(openai_tools)}` tools declared"
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "transcript_turns" not in st.session_state:
        st.session_state.transcript_turns = []
    if "transcript_meta" not in st.session_state:
        st.session_state.transcript_meta = {
            "transcript_id": f"{version}_{provider_name}_{datetime.now().strftime('%Y%m%dT%H%M%S%f')}",
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": model_override or getattr(provider, "default_model", None),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "turns": [],
        }

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Ask the research agent anything…")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.messages.append({"role": "user", "content": user_input})

        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "system"],
                window=5,
            ),
        ]

        try:
            result = run_one_turn(
                provider=provider,
                messages=messages,
                openai_tools=openai_tools,
                model=model_override or None,
                max_tool_rounds=max_rounds,
            )
        except Exception as exc:
            st.error(f"Provider error: {type(exc).__name__}: {exc}")
            return

        with st.chat_message("assistant"):
            st.markdown(result["assistant_text"])
            for round_record in result["rounds"]:
                _render_round(round_record, round_record["round"])

        st.session_state.messages.append({"role": "assistant", "content": result["assistant_text"]})
        st.session_state.transcript_turns.append({
            "turn_index": len(st.session_state.transcript_turns) + 1,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "user": user_input,
            **result,
        })
        st.session_state.transcript_meta["turns"] = st.session_state.transcript_turns

        path = save_transcript(version, provider_name, st.session_state.transcript_meta)
        st.caption(f"Transcript saved → `{path.name}`")

    with st.expander("Tools declared in this version", expanded=False):
        for tool in declarations:
            st.markdown(f"- **{tool['name']}** — {tool.get('description', '')[:140]}")


if __name__ == "__main__":
    main()
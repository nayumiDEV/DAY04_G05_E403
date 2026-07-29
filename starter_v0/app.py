from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def load_artifacts(version: str) -> dict:
    sys_prompt = ARTIFACTS_DIR / "system_prompt.md"
    tools_yaml = ARTIFACTS_DIR / "tools.yaml"
    prompt_text = sys_prompt.read_text(encoding="utf-8")
    decls = load_tool_declarations(tools_yaml)
    tools = to_openai_tools(decls)
    av = build_artifact_version(version, sys_prompt, tools_yaml)
    return {
        "system_prompt": prompt_text,
        "tools": tools,
        "artifact_version": av.artifact_version,
        "prompt_hash": av.prompt_hash[:12],
        "tools_hash": av.tools_hash[:12],
    }


def get_provider(name: str):
    return make_provider(name)


def save_transcript(transcript_id: str, artifact_version: str, prompt: str,
                    assistant_text: str, rounds: list[dict], tool_events: list[dict]) -> None:
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        "artifact_version": artifact_version,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "turns": [
            {
                "turn_index": 1,
                "started_at": datetime.now().isoformat(),
                "user": prompt,
                "status": "answered",
                "assistant_text": assistant_text,
                "rounds": rounds,
                "tool_events": tool_events,
                "ended_at": datetime.now().isoformat(),
            }
        ],
    }
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def render_tool_trace(rounds: list[dict]):
    for rnd in rounds:
        r = rnd["round"]
        status_badge = "✅" if rnd.get("tool_calls") else "⏸️"
        st.markdown(f"**{status_badge} Round {r}**")
        cols = st.columns([1, 2, 3])
        cols[0].markdown("**Tool**")
        cols[1].markdown("**Args**")
        cols[2].markdown("**Result**")
        for tc in rnd.get("tool_calls", []):
            st.markdown(f":blue-background[{tc['name']}]", unsafe_allow_html=False)
        for tr in rnd.get("tool_results", []):
            tool_name = tr.get("tool", "?")
            args_str = json.dumps(tr.get("args", {}), ensure_ascii=False)
            res = tr.get("result", {})
            if isinstance(res, dict):
                err = res.get("error")
                if err:
                    result_display = f":red[⚠️ {err}: {res.get('message', '')}]"
                elif res.get("awaiting_user"):
                    q = res.get("question", "")
                    result_display = f":blue[❓ {q[:100]}]"
                else:
                    summary = json.dumps(res, ensure_ascii=False)
                    if len(summary) > 150:
                        summary = summary[:150] + "..."
                    result_display = f":green[✅ {summary}]"
            else:
                result_display = f":green[✅ OK]"
            with st.container():
                c1, c2, c3 = st.columns([1, 2, 3])
                c1.code(tool_name)
                c2.markdown(f"```json\n{args_str[:200]}\n```")
                c3.markdown(result_display, unsafe_allow_html=False)
            st.divider()


st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")
st.title("🔍 Research Agent — Tool Eval Demo")

with st.sidebar:
    st.header("⚙️ Configuration")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    model_name = st.text_input("Model (optional)", value="", placeholder="gpt-4o-mini")
    version = st.selectbox("Artifact Version", ["v0", "v1", "v2", "v3"], index=3)

    if st.button("🚀 Load Agent", type="primary", use_container_width=True):
        st.session_state.provider = get_provider(provider_name)
        st.session_state.artifact = load_artifacts(version)
        st.session_state.messages = []
        st.session_state.rounds = []
        st.session_state.tool_events = []
        st.session_state.history = []
        st.session_state.transcript_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        st.rerun()

    if st.session_state.get("artifact"):
        st.divider()
        st.markdown("### 📦 Artifact")
        av = st.session_state.artifact
        st.metric("Version", av["artifact_version"])
        st.caption(f"Prompt: `{av['prompt_hash']}`")
        st.caption(f"Tools: `{av['tools_hash']}`")

    st.divider()
    st.markdown("### 📋 Version Compare")
    compare_mode = st.checkbox("Enable compare mode", value=False,
                                help="Run same prompt on multiple versions side-by-side")
    if compare_mode:
        compare_versions = st.multiselect("Versions to compare",
                                           ["v0", "v1", "v2", "v3"],
                                           default=["v0", "v3"])

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.rounds = []
        st.session_state.tool_events = []
        st.session_state.history = []
        st.rerun()

if not st.session_state.get("provider") or not st.session_state.get("artifact"):
    st.info("👈 Select provider & version, then click **Load Agent**.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Sample prompts to try:")
        st.code('"Tweet mới nhất của Sam Altman là gì?"')
        st.code('"Tin tức AI hôm nay có gì nổi bật?"')
        st.code('"Thời tiết Hà Nội thế nào?"')
    with col2:
        st.markdown("#### Edge case prompts:")
        st.code('"Tóm tắt bài này hộ mình"  (thiếu URL → clarify)')
        st.code('"Đăng bản tin này lên Telegram"  (cần xác nhận)')
        st.code('"Giải phương trình x^2+1=0"  (out-of-scope)')
    st.stop()


# ---- Main chat area ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("Type your research request..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if compare_mode:
        tabs = st.tabs([f"**{v}**" for v in compare_versions])
        for ti, cv in enumerate(compare_versions):
            with tabs[ti]:
                with st.spinner(f"Running on {cv}..."):
                    try:
                        art = load_artifacts(cv)
                        full = [
                            {"role": "system", "content": art["system_prompt"]},
                            *st.session_state.history[-10:],
                            {"role": "user", "content": prompt},
                        ]
                        res = run_model_tool_loop(
                            provider=st.session_state.provider,
                            messages=full,
                            tools=art["tools"],
                            model=model_name or None,
                            max_tool_rounds=4,
                        )
                        st.markdown(f"**Response:** {res['assistant_text']}")
                        if res.get("rounds"):
                            with st.expander(f"🔧 Tool Trace ({len(res['rounds'])} rounds)", expanded=True):
                                render_tool_trace(res["rounds"])
                        st.caption(f"Artifact: {art['artifact_version']}")
                        save_transcript(
                            transcript_id=f"{cv}_{st.session_state.get('transcript_id', 'run')}",
                            artifact_version=art["artifact_version"],
                            prompt=prompt,
                            assistant_text=res["assistant_text"],
                            rounds=res.get("rounds", []),
                            tool_events=res.get("tool_events", []),
                        )
                    except Exception as exc:
                        st.error(f"{type(exc).__name__}: {exc}")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Running agent..."):
                try:
                    full_messages = [
                        {"role": "system", "content": st.session_state.artifact["system_prompt"]},
                        *st.session_state.history[-10:],
                        {"role": "user", "content": prompt},
                    ]
                    result = run_model_tool_loop(
                        provider=st.session_state.provider,
                        messages=full_messages,
                        tools=st.session_state.artifact["tools"],
                        model=model_name or None,
                        max_tool_rounds=4,
                    )
                    assistant_text = result["assistant_text"]
                    rounds = result["rounds"]
                    tool_events = result["tool_events"]

                    st.markdown(assistant_text)

                    if rounds:
                        with st.expander(f"🔧 Tool Trace ({len(rounds)} round(s))", expanded=True):
                            render_tool_trace(rounds)

                    if tool_events:
                        st.download_button(
                            label="📥 Download Transcript JSON",
                            data=json.dumps({
                                "prompt": prompt,
                                "response": assistant_text,
                                "artifact_version": st.session_state.artifact["artifact_version"],
                                "rounds": rounds,
                                "tool_events": tool_events,
                                "timestamp": datetime.now().isoformat(),
                            }, ensure_ascii=False, indent=2),
                            file_name=f"transcript_{st.session_state.get('transcript_id', 'run')}.json",
                            mime="application/json",
                        )

                    save_transcript(
                        transcript_id=st.session_state.get("transcript_id", "run"),
                        artifact_version=st.session_state.artifact["artifact_version"],
                        prompt=prompt,
                        assistant_text=assistant_text,
                        rounds=rounds,
                        tool_events=tool_events,
                    )

                    st.session_state.rounds = rounds
                    st.session_state.tool_events = tool_events
                    st.session_state.history.append({"role": "user", "content": prompt})
                    st.session_state.history.append({"role": "assistant", "content": assistant_text})
                    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

                except Exception as exc:
                    st.error(f"{type(exc).__name__}: {exc}")

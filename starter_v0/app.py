"""
Research Agent — Streamlit UI
Reuses run_model_tool_loop from chat.py as required by the lab spec.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ── paths ──
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"

# Ensure importable
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict
from chat import run_model_tool_loop, write_transcript, safe_slug, now_iso

load_lab_env(ROOT)

# ─────────────────────── Page Config ───────────────────────
st.set_page_config(
    page_title="🔬 Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────── Custom CSS ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1333 40%, #24243e 100%);
}
header[data-testid="stHeader"] { background: transparent; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #16132b 0%, #1c1940 100%) !important;
    border-right: 1px solid rgba(139,92,246,0.15);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #c4b5fd !important;
}
section[data-testid="stSidebar"] label { color: #a5b4fc !important; }

/* ── Glass card ── */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

/* ── Chat messages ── */
.user-msg {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.10));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0;
    color: #e0e7ff;
    animation: slideIn 0.3s ease;
}
.agent-msg {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(139,92,246,0.12);
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0;
    color: #e2e8f0;
    animation: slideIn 0.3s ease;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Tool trace ── */
.tool-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 6px;
}
.tool-success { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.tool-error { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.tool-waiting { background: rgba(251,191,36,0.15); color: #fde68a; border: 1px solid rgba(251,191,36,0.3); }

/* ── Metric cards ── */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.metric-value { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
.metric-label { font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 10px;
    color: #a5b4fc;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15)) !important;
    border-color: rgba(139,92,246,0.4) !important;
    color: #e0e7ff !important;
}

/* ── Expander ── */
.streamlit-expanderHeader { color: #c4b5fd !important; font-weight: 500; }
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(139,92,246,0.12);
    border-radius: 12px;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    color: #e2e8f0 !important;
    border-radius: 12px !important;
}
button[kind="primary"], .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
button[kind="primary"]:hover, .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
}

/* ── Status ── */
.status-answered { color: #6ee7b7; }
.status-waiting { color: #fde68a; }
.status-error { color: #fca5a5; }

/* ── Hero title ── */
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #6366f1, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.hero-sub { color: #94a3b8; font-size: 0.95rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────── Helpers ───────────────────────
def render_tool_trace(rounds: list[dict], tool_events: list[dict]) -> None:
    """Display tool trace with colored badges."""
    if not rounds:
        return
    for r in rounds:
        rnd = r.get("round", "?")
        calls = r.get("tool_calls", [])
        results = r.get("tool_results", [])
        if not calls:
            continue
        with st.expander(f"🔧 Round {rnd} — {len(calls)} tool call(s)", expanded=False):
            for i, call in enumerate(calls):
                name = call.get("name", "?")
                args = call.get("args", {})
                res = results[i] if i < len(results) else {}
                result_data = res.get("result", {})
                is_err = isinstance(result_data, dict) and "error" in result_data
                is_wait = isinstance(result_data, dict) and result_data.get("awaiting_user")
                if is_err:
                    badge = '<span class="tool-badge tool-error">❌ error</span>'
                elif is_wait:
                    badge = '<span class="tool-badge tool-waiting">⏳ awaiting user</span>'
                else:
                    badge = '<span class="tool-badge tool-success">✅ success</span>'
                st.markdown(f"**`{name}`** {badge}", unsafe_allow_html=True)
                st.json({"args": args}, expanded=False)
                if result_data:
                    st.json({"result": result_data}, expanded=False)


def render_chat_message(role: str, content: str, rounds=None, tool_events=None) -> None:
    """Render a single chat message with optional tool trace."""
    if role == "user":
        st.markdown(f'<div class="user-msg">👤 <strong>You</strong><br>{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="agent-msg">🤖 <strong>Agent</strong><br>{content}</div>', unsafe_allow_html=True)
        if rounds:
            render_tool_trace(rounds, tool_events or [])


def load_json_safe(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_json_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


# ─────────────────────── Sidebar ───────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title">🔬 Research Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Evidence-driven tool evaluation</div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ Configuration")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0, key="provider")
    version_label = st.selectbox("Version", ["v0", "v1", "v2", "v3"], index=3, key="version")
    custom_model = st.text_input("Model (blank = default)", value="", key="model")
    max_rounds = st.slider("Max tool rounds", 1, 8, 4, key="max_rounds")

    st.markdown("---")

    # Build artifact version info
    sp_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    if sp_path.exists() and tools_path.exists():
        av = build_artifact_version(version_label, sp_path, tools_path)
        st.markdown("### 📋 Artifact Info")
        st.code(f"version: {av.version}\nartifact: {av.artifact_version}\nprompt_hash: {av.prompt_hash[:16]}\ntools_hash: {av.tools_hash[:16]}", language="yaml")

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.pop("messages", None)
        st.session_state.pop("transcript", None)
        st.rerun()


# ─────────────────────── Init Session ───────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None


# ─────────────────────── Main Tabs ───────────────────────
tab_chat, tab_transcripts, tab_runs, tab_compare = st.tabs([
    "💬 Chat", "📜 Transcripts", "📊 Runs", "🔀 Compare Versions"
])

# ━━━━━━━━━━━━━━━━━━━━━ TAB: CHAT ━━━━━━━━━━━━━━━━━━━━━
with tab_chat:
    st.markdown('<div class="hero-title">💬 Live Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Chat with the Research Agent in real-time</div>', unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.messages:
        render_chat_message(
            msg["role"], msg["content"],
            msg.get("rounds"), msg.get("tool_events")
        )

    # Chat input
    user_input = st.chat_input("Ask the Research Agent something...")

    if user_input:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_chat_message("user", user_input)

        # Prepare provider & tools
        try:
            provider = make_provider(provider_name)
            system_prompt = sp_path.read_text(encoding="utf-8")
            tool_decls = load_tool_declarations(tools_path)
            openai_tools = to_openai_tools(tool_decls)
            model = custom_model or None

            # Build conversation messages
            history_msgs = []
            for m in st.session_state.messages[:-1]:
                if m["role"] in ("user", "assistant"):
                    history_msgs.append({"role": m["role"], "content": m["content"]})

            messages = [
                {"role": "system", "content": system_prompt},
                *history_msgs[-10:],
                {"role": "user", "content": user_input},
            ]

            with st.spinner("🔄 Agent is thinking..."):
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model,
                    max_tool_rounds=max_rounds,
                )

            assistant_text = result.get("assistant_text", "")
            status = result.get("status", "unknown")
            rounds = result.get("rounds", [])
            tool_events = result.get("tool_events", [])

            # Save assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "status": status,
                "rounds": rounds,
                "tool_events": tool_events,
            })

            # Save transcript
            if st.session_state.transcript is None:
                av_obj = build_artifact_version(version_label, sp_path, tools_path)
                ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
                tid = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{ts}"
                st.session_state.transcript = {
                    "transcript_id": tid,
                    **artifact_version_dict(av_obj),
                    "provider": provider_name,
                    "model": model or getattr(provider, "default_model", None),
                    "system_prompt": str(sp_path),
                    "tools": str(tools_path),
                    "history_window": 5,
                    "max_tool_rounds": max_rounds,
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "turns": [],
                }

            turn_record = {
                "turn_index": len(st.session_state.transcript["turns"]) + 1,
                "started_at": now_iso(),
                "user": user_input,
                **result,
                "ended_at": now_iso(),
            }
            st.session_state.transcript["turns"].append(turn_record)

            t_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript['transcript_id']}.transcript.json"
            write_transcript(t_path, st.session_state.transcript)

            st.rerun()

        except Exception as exc:
            st.error(f"❌ Error: {type(exc).__name__}: {exc}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Error: {exc}",
                "status": "error",
                "rounds": [],
                "tool_events": [],
            })

# ━━━━━━━━━━━━━━━━━━━━━ TAB: TRANSCRIPTS ━━━━━━━━━━━━━━━━━━━━━
with tab_transcripts:
    st.markdown('<div class="hero-title">📜 Transcripts</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Browse saved conversation transcripts</div>', unsafe_allow_html=True)

    files = list_json_files(TRANSCRIPTS_DIR)
    if not files:
        st.info("No transcripts yet. Start chatting to generate one!")
    else:
        selected_file = st.selectbox("Select transcript", files, format_func=lambda p: p.name)
        data = load_json_safe(selected_file)
        if data:
            # Metadata
            cols = st.columns(4)
            cols[0].markdown(f'<div class="metric-card"><div class="metric-value">{data.get("version", "?")}</div><div class="metric-label">Version</div></div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div class="metric-card"><div class="metric-value">{len(data.get("turns", []))}</div><div class="metric-label">Turns</div></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="metric-card"><div class="metric-value">{data.get("provider", "?")}</div><div class="metric-label">Provider</div></div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div class="metric-card"><div class="metric-value">{data.get("model", "?")[:20]}</div><div class="metric-label">Model</div></div>', unsafe_allow_html=True)

            st.markdown("---")
            for turn in data.get("turns", []):
                render_chat_message("user", turn.get("user", ""))
                render_chat_message(
                    "assistant", turn.get("assistant_text", ""),
                    turn.get("rounds", []), turn.get("tool_events", [])
                )
                status = turn.get("status", "unknown")
                cls = "status-answered" if status == "answered" else "status-waiting" if "waiting" in status else "status-error"
                st.markdown(f'<small class="{cls}">Status: {status}</small>', unsafe_allow_html=True)
                st.markdown("---")

# ━━━━━━━━━━━━━━━━━━━━━ TAB: RUNS ━━━━━━━━━━━━━━━━━━━━━
with tab_runs:
    st.markdown('<div class="hero-title">📊 Eval Runs</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Inspect evaluation run results and metrics</div>', unsafe_allow_html=True)

    run_files = list_json_files(RUNS_DIR)
    if not run_files:
        st.info("No run files yet. Run eval first: `python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json`")
    else:
        selected_run = st.selectbox("Select run", run_files, format_func=lambda p: p.name)
        run_data = load_json_safe(selected_run)
        if run_data:
            summary = run_data.get("summary", {})

            # Metrics dashboard
            st.markdown("### 📈 Summary Metrics")
            mcols = st.columns(4)
            metrics = [
                ("Case Accuracy", summary.get("case_accuracy", "N/A")),
                ("Tool Routing", summary.get("tool_routing_accuracy", "N/A")),
                ("Argument Acc.", summary.get("argument_accuracy", "N/A")),
                ("Multi-turn", summary.get("multiturn_accuracy", "N/A")),
            ]
            for i, (label, val) in enumerate(metrics):
                if isinstance(val, float):
                    val = f"{val:.1%}"
                mcols[i].markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

            extra_cols = st.columns(3)
            extra_cols[0].metric("Provider Errors", summary.get("provider_error_cases", "?"))
            extra_cols[1].metric("Measured Cases", summary.get("measured_cases", "?"))
            extra_cols[2].metric("Total Cases", summary.get("total_cases", "?"))

            # Per-case details
            st.markdown("### 🔍 Per-Case Results")
            results = run_data.get("results", [])
            for case in results:
                case_id = case.get("case_id", "?")
                res = case.get("result", {})
                passed = res.get("pass", False)
                icon = "✅" if passed else "❌"
                with st.expander(f"{icon} {case_id}", expanded=not passed):
                    if res.get("failures"):
                        st.error("Failures: " + "; ".join(res["failures"]))
                    if res.get("observed_mismatch"):
                        st.warning("Mismatch: " + json.dumps(res["observed_mismatch"], ensure_ascii=False))
                    actual = case.get("actual_tool_calls", res.get("actual_tool_calls", []))
                    if actual:
                        st.markdown("**Actual tool calls:**")
                        st.json(actual, expanded=False)
                    tool_res = case.get("tool_results", res.get("tool_results", []))
                    if tool_res:
                        st.markdown("**Tool results:**")
                        st.json(tool_res, expanded=False)

# ━━━━━━━━━━━━━━━━━━━━━ TAB: COMPARE ━━━━━━━━━━━━━━━━━━━━━
with tab_compare:
    st.markdown('<div class="hero-title">🔀 Compare Versions</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Side-by-side comparison of eval runs across versions</div>', unsafe_allow_html=True)

    run_files = list_json_files(RUNS_DIR)
    if len(run_files) < 2:
        st.info("Need at least 2 run files to compare. Run eval for different versions first.")
    else:
        col_l, col_r = st.columns(2)
        with col_l:
            left_file = st.selectbox("Left run", run_files, format_func=lambda p: p.name, key="cmp_left")
        with col_r:
            right_file = st.selectbox("Right run", run_files, index=min(1, len(run_files)-1), format_func=lambda p: p.name, key="cmp_right")

        left_data = load_json_safe(left_file)
        right_data = load_json_safe(right_file)

        if left_data and right_data:
            ls = left_data.get("summary", {})
            rs = right_data.get("summary", {})

            st.markdown("### 📊 Metrics Comparison")
            compare_metrics = ["case_accuracy", "tool_routing_accuracy", "argument_accuracy", "multiturn_accuracy"]
            header_cols = st.columns([2, 1, 1, 1])
            header_cols[0].markdown("**Metric**")
            header_cols[1].markdown(f"**{left_file.stem[:25]}**")
            header_cols[2].markdown(f"**{right_file.stem[:25]}**")
            header_cols[3].markdown("**Delta**")

            for m in compare_metrics:
                lv = ls.get(m)
                rv = rs.get(m)
                row = st.columns([2, 1, 1, 1])
                row[0].write(m.replace("_", " ").title())
                lstr = f"{lv:.1%}" if isinstance(lv, (int, float)) else str(lv)
                rstr = f"{rv:.1%}" if isinstance(rv, (int, float)) else str(rv)
                row[1].write(lstr)
                row[2].write(rstr)
                if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
                    delta = rv - lv
                    color = "🟢" if delta > 0 else "🔴" if delta < 0 else "⚪"
                    row[3].write(f"{color} {delta:+.1%}")
                else:
                    row[3].write("—")

            # Per-case diff
            st.markdown("### 🔍 Per-Case Comparison")
            left_results = {c.get("case_id"): c for c in left_data.get("results", [])}
            right_results = {c.get("case_id"): c for c in right_data.get("results", [])}
            all_ids = sorted(set(list(left_results.keys()) + list(right_results.keys())))

            for cid in all_ids:
                lc = left_results.get(cid, {})
                rc = right_results.get(cid, {})
                lp = lc.get("result", {}).get("pass", False)
                rp = rc.get("result", {}).get("pass", False)
                if lp and rp:
                    icon = "✅✅"
                elif not lp and rp:
                    icon = "❌→✅"
                elif lp and not rp:
                    icon = "✅→❌"
                else:
                    icon = "❌❌"
                with st.expander(f"{icon} {cid}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Left** {'✅' if lp else '❌'}")
                        if lc.get("result", {}).get("failures"):
                            st.error("; ".join(lc["result"]["failures"]))
                    with c2:
                        st.markdown(f"**Right** {'✅' if rp else '❌'}")
                        if rc.get("result", {}).get("failures"):
                            st.error("; ".join(rc["result"]["failures"]))

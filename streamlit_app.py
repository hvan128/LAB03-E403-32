import os
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

from main import MODE_LABELS, build_systems

load_dotenv()

st.set_page_config(
    page_title="Lab 3 - Product Comparison Assistant",
    page_icon="🛍️",
    layout="wide",
)


FLOW_CSS = """
<style>
* { box-sizing: border-box; }
body { margin: 0; padding: 0; background: transparent; }
.flow-container {
    display: flex; flex-direction: column; align-items: center;
    gap: 0; padding: 12px 6px;
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
}
.flow-node {
    width: 95%; max-width: 600px; border-radius: 10px;
    padding: 12px 16px; position: relative;
    box-shadow: 0 1px 6px rgba(0,0,0,0.15);
}
.node-header {
    font-weight: 700; font-size: 13px; margin-bottom: 4px;
    display: flex; align-items: center; gap: 6px;
}
.node-body {
    font-size: 12.5px; line-height: 1.5;
    word-wrap: break-word; white-space: pre-wrap;
}
.node-meta {
    font-size: 10.5px; margin-top: 6px;
    display: flex; gap: 8px; flex-wrap: wrap;
}
.node-meta span {
    padding: 2px 7px; border-radius: 4px;
    font-weight: 500;
}
.flow-arrow {
    display: flex; flex-direction: column; align-items: center; height: 28px;
}
.arrow-line { width: 2px; height: 18px; }
.arrow-head {
    width: 0; height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
}
.step-badge {
    padding: 1px 8px; border-radius: 10px;
    font-size: 10px; font-weight: 600;
}

/* --- Light-friendly color scheme --- */
.node-input {
    background: #e8f0fe; border: 2px solid #4285f4; color: #1a3e72;
}
.node-input .node-meta span { background: rgba(66,133,244,0.15); }

.node-thought {
    background: #fef3e0; border: 2px solid #f9a825; color: #5d4200;
}
.node-thought .node-meta span { background: rgba(249,168,37,0.15); }
.node-thought .step-badge { background: rgba(249,168,37,0.25); }

.node-action {
    background: #ede7f6; border: 2px solid #7c4dff; color: #311b72;
}
.node-action .step-badge { background: rgba(124,77,255,0.2); }

.node-observation {
    background: #e8f5e9; border: 2px solid #43a047; color: #1b5e20;
}

.node-error {
    background: #fce4ec; border: 2px solid #e53935; color: #7f0000;
}
.node-error .node-meta span { background: rgba(229,57,53,0.12); }
.node-error .step-badge { background: rgba(229,57,53,0.2); }

.node-final-success {
    background: #e8f5e9; border: 3px solid #2e7d32; color: #1b5e20;
}
.node-final-success .node-meta span { background: rgba(46,125,50,0.12); }

.node-final-fail {
    background: #fff3e0; border: 3px solid #e65100; color: #4e2700;
}
.node-final-fail .node-meta span { background: rgba(230,81,0,0.12); }

.arrow-line { background: #bdbdbd; }
.arrow-head { border-top: 8px solid #bdbdbd; }

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .node-input {
        background: #1a3150; border-color: #5c9cf5; color: #cfe0fc;
    }
    .node-input .node-meta span { background: rgba(92,156,245,0.2); }

    .node-thought {
        background: #3e2e0a; border-color: #f5a623; color: #fde8b8;
    }
    .node-thought .node-meta span { background: rgba(245,166,35,0.2); }
    .node-thought .step-badge { background: rgba(245,166,35,0.3); }

    .node-action {
        background: #2a1f4e; border-color: #a29bfe; color: #ddd6fe;
    }
    .node-action .step-badge { background: rgba(162,155,254,0.25); }

    .node-observation {
        background: #0f2e16; border-color: #4caf50; color: #c8e6c9;
    }

    .node-error {
        background: #3e0a0a; border-color: #ff6b6b; color: #ffcdd2;
    }
    .node-error .node-meta span { background: rgba(255,107,107,0.2); }
    .node-error .step-badge { background: rgba(255,107,107,0.25); }

    .node-final-success {
        background: #0f2e16; border-color: #4caf50; color: #c8e6c9;
    }
    .node-final-success .node-meta span { background: rgba(76,175,80,0.2); }

    .node-final-fail {
        background: #3e2000; border-color: #ff9800; color: #ffe0b2;
    }
    .node-final-fail .node-meta span { background: rgba(255,152,0,0.2); }

    .arrow-line { background: #616161; }
    .arrow-head { border-top-color: #616161; }
}
</style>
"""


@st.cache_resource
def get_systems():
    return build_systems()


def reset_chat_if_mode_changed(selected_mode: str) -> None:
    if st.session_state.get("selected_mode") != selected_mode:
        st.session_state.selected_mode = selected_mode
        st.session_state.messages = []


def _esc(text: str) -> str:
    text = str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace('"', "&quot;").replace("'", "&#39;")
    return text


def _trunc(text: str, n: int = 120) -> str:
    text = str(text).replace("\n", " ")
    return text[:n] + "..." if len(text) > n else text


def build_html_flowchart(trace: list) -> str:
    """Build a visual HTML/CSS flowchart from agent trace."""
    nodes_html = []

    for i, entry in enumerate(trace):
        t = entry["type"]

        if i > 0:
            nodes_html.append(
                '<div class="flow-arrow"><div class="arrow-line"></div>'
                '<div class="arrow-head"></div></div>'
            )

        if t == "input":
            nodes_html.append(f'''
            <div class="flow-node node-input">
                <div class="node-header">🔵 User Input</div>
                <div class="node-body">{_esc(_trunc(entry["content"], 200))}</div>
            </div>''')

        elif t == "thought":
            step = entry.get("step", "?")
            tokens = entry.get("tokens", {})
            lat = entry.get("latency_ms", 0)
            nodes_html.append(f'''
            <div class="flow-node node-thought">
                <div class="node-header">
                    💭 Thought <span class="step-badge">Step {step}</span>
                </div>
                <div class="node-body">{_esc(_trunc(entry.get("content", ""), 200))}</div>
                <div class="node-meta">
                    <span>⏱ {lat}ms</span>
                    <span>Prompt: {tokens.get("prompt_tokens", 0)}</span>
                    <span>Completion: {tokens.get("completion_tokens", 0)}</span>
                    <span>Total: {tokens.get("total_tokens", 0)}</span>
                </div>
            </div>''')

        elif t == "action":
            step = entry.get("step", "?")
            tool = entry.get("tool", "?")
            arg = entry.get("arg", "")
            obs = entry.get("observation", "")
            nodes_html.append(f'''
            <div class="flow-node node-action">
                <div class="node-header">
                    🔧 Tool Call <span class="step-badge">Step {step}</span>
                </div>
                <div class="node-body"><strong>{_esc(tool)}</strong>({_esc(_trunc(arg, 80))})</div>
            </div>''')
            nodes_html.append(
                '<div class="flow-arrow"><div class="arrow-line"></div>'
                '<div class="arrow-head"></div></div>'
            )
            nodes_html.append(f'''
            <div class="flow-node node-observation">
                <div class="node-header">📋 Observation</div>
                <div class="node-body">{_esc(_trunc(obs, 250))}</div>
            </div>''')

        elif t == "error":
            step = entry.get("step", "?")
            err_type = entry.get("error_type", "error")
            tokens = entry.get("tokens", {})
            lat = entry.get("latency_ms", 0)
            nodes_html.append(f'''
            <div class="flow-node node-error">
                <div class="node-header">
                    ❌ {_esc(err_type.upper())} <span class="step-badge">Step {step}</span>
                </div>
                <div class="node-body">{_esc(_trunc(entry.get("content", ""), 200))}</div>
                <div class="node-meta">
                    <span>⏱ {lat}ms</span>
                    <span>Tokens: {tokens.get("total_tokens", 0)}</span>
                </div>
            </div>''')

        elif t == "final_answer":
            status = entry.get("status", "?")
            total_tok = entry.get("total_tokens", {})
            total_lat = entry.get("total_latency_ms", 0)
            loop_count = entry.get("step", "?")
            cls = "node-final-success" if status == "success" else "node-final-fail"
            icon = "✅" if status == "success" else "⚠️"
            total_t = total_tok.get("total_tokens", 0)
            cost = total_t / 1000 * 0.01
            nodes_html.append(f'''
            <div class="flow-node {cls}">
                <div class="node-header">{icon} Final Answer</div>
                <div class="node-body">{_esc(_trunc(entry.get("content", ""), 300))}</div>
                <div class="node-meta">
                    <span>🔁 Loops: {loop_count}</span>
                    <span>⏱ {total_lat}ms</span>
                    <span>Prompt: {total_tok.get("prompt_tokens", 0)}</span>
                    <span>Completion: {total_tok.get("completion_tokens", 0)}</span>
                    <span>Total: {total_t}</span>
                    <span>💰 ~${cost:.4f}</span>
                </div>
            </div>''')

    body = "\n".join(nodes_html)
    return f"""<!DOCTYPE html><html><head>{FLOW_CSS}</head>
    <body><div class="flow-container">{body}</div></body></html>"""


def _calc_height(trace: list) -> int:
    num_visual = 0
    for e in trace:
        if e["type"] == "action":
            num_visual += 3
        else:
            num_visual += 1
    num_visual += max(0, len(trace) - 1)
    return max(300, num_visual * 80)


def main() -> None:
    st.title("🛍️ Trợ lý so sánh sản phẩm")
    st.caption("Baseline Chatbot • ReAct Agent v1 • ReAct Agent v2")

    systems = get_systems()

    with st.sidebar:
        st.header("⚙️ Cấu hình")
        selected_mode = st.selectbox(
            "Chọn chế độ",
            options=["chatbot", "v1", "v2"],
            format_func=lambda mode: MODE_LABELS[mode],
        )
        compare_all = st.checkbox("So sánh cả 3 chế độ", value=False)

        st.markdown("---")
        st.write(f"**Provider:** `{os.getenv('DEFAULT_PROVIDER', 'openai')}`")
        st.write(f"**Model:** `{os.getenv('DEFAULT_MODEL', 'gpt-4o')}`")

        if st.button("🧹 Xóa hội thoại"):
            st.session_state.messages = []
            if "last_trace_mode" in st.session_state:
                del st.session_state["last_trace_mode"]
            st.rerun()

        st.markdown("### 💡 Gợi ý câu hỏi")
        sample_prompts = [
            "So sánh iPhone 15 và Samsung Galaxy S24",
            "MacBook Air M2 và Dell XPS 13 cái nào rẻ hơn?",
            "iPhone 15 Pro Max giảm giá 20%?",
            "Samsung S24 Ultra giá bao nhiêu USD?",
            "Tìm các laptop có sẵn",
        ]
        for prompt in sample_prompts:
            if st.button(prompt, use_container_width=True):
                st.session_state.pending_prompt = prompt

    reset_chat_if_mode_changed(selected_mode)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # === Two-column layout ===
    col_chat, col_flow = st.columns([1, 1], gap="large")

    with col_chat:
        st.markdown("### 💬 Chat")
        chat_container = st.container(height=550)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        prompt = st.session_state.pop("pending_prompt", None) or st.chat_input(
            "Nhập câu hỏi về sản phẩm..."
        )

    with col_flow:
        st.markdown("### 🔄 ReAct Flowchart")
        flow_placeholder = st.empty()

    # --- Process prompt ---
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with col_chat:
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

        # Realtime callback: update flowchart on each agent step
        def on_step(trace_snapshot):
            html = build_html_flowchart(trace_snapshot)
            height = _calc_height(trace_snapshot)
            with flow_placeholder.container():
                components.html(html, height=height, scrolling=True)

        # Show placeholder while processing
        if selected_mode in ("v1", "v2") and not compare_all:
            flow_placeholder.info("⏳ Đang chờ agent xử lý...")

        with col_chat:
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Đang xử lý..."):
                        try:
                            if compare_all:
                                outputs = []
                                for mode_key in ["chatbot", "v1", "v2"]:
                                    answer = systems[mode_key].run(prompt)
                                    outputs.append(f"**{MODE_LABELS[mode_key]}:**\n{answer}")
                                reply = "\n\n---\n\n".join(outputs)
                            else:
                                if selected_mode == "chatbot":
                                    reply = systems["chatbot"].run(prompt)
                                else:
                                    reply = systems[selected_mode].run(
                                        prompt, on_step=on_step
                                    )
                        except Exception as exc:
                            reply = f"❌ Error: {exc}"

                    st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.last_trace_mode = selected_mode
        st.session_state.last_compare_all = compare_all

        # Final flowchart render (compare mode)
        if compare_all:
            with col_flow:
                for mk in ["v1", "v2"]:
                    trace = getattr(systems[mk], "trace", [])
                    if trace:
                        st.markdown(f"#### {MODE_LABELS[mk]}")
                        html = build_html_flowchart(trace)
                        components.html(html, height=_calc_height(trace), scrolling=True)
                        with st.expander(f"🗂️ Raw Trace — {MODE_LABELS[mk]}"):
                            st.json(trace)
        else:
            # Show raw trace expander for single mode
            if selected_mode in ("v1", "v2"):
                trace = getattr(systems[selected_mode], "trace", [])
                if trace:
                    with col_flow:
                        with st.expander("🗂️ Raw Trace JSON"):
                            st.json(trace)

    else:
        # No prompt — show last trace or placeholder
        trace_mode = st.session_state.get("last_trace_mode", selected_mode)
        is_compare = st.session_state.get("last_compare_all", False)

        if is_compare:
            with col_flow:
                for mk in ["v1", "v2"]:
                    trace = getattr(systems[mk], "trace", [])
                    if trace:
                        st.markdown(f"#### {MODE_LABELS[mk]}")
                        html = build_html_flowchart(trace)
                        components.html(html, height=_calc_height(trace), scrolling=True)
        else:
            trace = getattr(systems.get(trace_mode), "trace", []) if systems.get(trace_mode) else []
            if trace:
                html = build_html_flowchart(trace)
                with flow_placeholder.container():
                    components.html(html, height=_calc_height(trace), scrolling=True)
            else:
                flow_placeholder.markdown(
                    '<div style="display:flex;align-items:center;justify-content:center;'
                    'height:300px;color:#888;font-size:15px;">'
                    "Gửi câu hỏi ở chế độ Agent v1/v2 để xem flowchart"
                    "</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()

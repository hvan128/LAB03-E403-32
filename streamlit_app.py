import os
from dotenv import load_dotenv
import streamlit as st

from main import MODE_LABELS, build_systems

load_dotenv()

st.set_page_config(
    page_title="Lab 3 - Product Comparison Assistant",
    page_icon="🛍️",
    layout="wide",
)


@st.cache_resource
def get_systems():
    return build_systems()


def reset_chat_if_mode_changed(selected_mode: str) -> None:
    if st.session_state.get("selected_mode") != selected_mode:
        st.session_state.selected_mode = selected_mode
        st.session_state.messages = []


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
            st.rerun()

        st.markdown("### 💡 Gợi ý câu hỏi")
        sample_prompts = [
            "So sánh iPhone 15 và Samsung Galaxy S24",
            "MacBook Air M2 và Dell XPS 13 cái nào rẻ hơn bao nhiêu tiền?",
            "iPhone 15 Pro Max giảm giá 20%, giá còn bao nhiêu?",
        ]
        for prompt in sample_prompts:
            if st.button(prompt, use_container_width=True):
                st.session_state.pending_prompt = prompt

    reset_chat_if_mode_changed(selected_mode)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.session_state.pop("pending_prompt", None) or st.chat_input("Nhập câu hỏi về sản phẩm...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Đang xử lý..."):
                try:
                    if compare_all:
                        outputs = []
                        for mode_key in ["chatbot", "v1", "v2"]:
                            answer = systems[mode_key].run(prompt)
                            outputs.append(f"### {MODE_LABELS[mode_key]}\n{answer}")
                        reply = "\n\n".join(outputs)
                    else:
                        reply = systems[selected_mode].run(prompt)
                except Exception as exc:
                    reply = f"❌ Error: {exc}"

            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()

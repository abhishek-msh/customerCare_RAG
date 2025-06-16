import streamlit as st
import requests
import uuid
import json

# -----------------------------------------------------------------------------
# Page configuration – must be first Streamlit command
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Cyfuture AI Chatbot", page_icon="🤖", layout="centered")

"""
Cyfuture AI Chatbot – Streamlit UI
---------------------------------
Launch with:

    streamlit run streamlit_chatbot_ui.py
"""

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
API_URL = "http://localhost:8083/chatbot"  # Adjust if FastAPI host/port differ

# -----------------------------------------------------------------------------
# Poly‑fill: Streamlit 1.32+ renamed experimental_rerun() → rerun()
# -----------------------------------------------------------------------------
_RERUN = getattr(st, "rerun", getattr(st, "experimental_rerun", None))

# -----------------------------------------------------------------------------
# Session-state bootstrap
# -----------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages: list[dict[str, str]] = []

# -----------------------------------------------------------------------------
# 📄 Helper – pretty complaint details (robust)
# -----------------------------------------------------------------------------


def _fmt_complaint_details(details) -> str:
    if not details:
        return ""
    if not isinstance(details, dict):
        return f"\n\n**Complaint details**\n{details}\n"
    md = "\n\n**Complaint details**\n"
    for k, v in details.items():
        md += f"- **{k.replace('_', ' ').title()}**: {v}\n"
    return md


# -----------------------------------------------------------------------------
# 🤖 Helper – normalise backend payloads → markdown
# -----------------------------------------------------------------------------


def _extract_bot_text(payload) -> str:
    def _join(main: str, details):
        return main + _fmt_complaint_details(details)

    # 1 & 2 – modern wrapper
    if isinstance(payload, dict) and "bot_response" in payload:
        bot = payload["bot_response"]
        if isinstance(bot, str):
            return bot
        if isinstance(bot, dict):
            return _join(bot.get("response", ""), bot.get("complaint_details"))

    # 3 – old schema
    if isinstance(payload, dict) and "response" in payload:
        return _join(payload.get("response", ""), payload.get("complaint_details"))

    return json.dumps(payload, indent=2)


# -----------------------------------------------------------------------------
# Sidebar – session controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔐 Session ID")
    st.code(st.session_state.user_id, language="")

    if st.button("🔄 New session", use_container_width=True):
        st.session_state.clear()
        st.session_state.user_id = str(uuid.uuid4())
        if _RERUN:
            _RERUN()

    st.markdown("---")
    st.caption("Made with ❤️ for Cyfuture AI Bot")

# -----------------------------------------------------------------------------
# Main – chat interface
# -----------------------------------------------------------------------------
st.title("Cyfuture AI Chatbot 🤝")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask me anything …"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        resp = requests.post(
            API_URL,
            json={"user_id": st.session_state.user_id, "user_text": prompt},
            timeout=60,
        )
        resp.raise_for_status()
        raw_data = resp.json()
    except requests.exceptions.RequestException as exc:
        raw_data = {"error": str(exc)}

    bot_text = _extract_bot_text(raw_data)

    st.session_state.messages.append({"role": "assistant", "content": bot_text})
    with st.chat_message("assistant"):
        st.markdown(bot_text, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
with st.expander("ℹ️ How it works"):
    st.markdown(
        """
        * Supports both old and new backend schemas.
        * `Complaint details` rendered only when present.
        * Compatible with Streamlit versions **<1.32** (experimental_rerun) and **≥1.32** (rerun).
        """
    )

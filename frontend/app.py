import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="SmartDoc – Document Analyzer", page_icon="📄")

# ==========================================
# 💄 Optional Chat Bubble Styling
# ==========================================
st.markdown("""
<style>
/* Create a fixed footer area inside the sidebar */
.sidebar-delete-container {
    position: fixed;
    bottom: 20px;
    left: 0;
    width: 18rem;         /* matches Streamlit sidebar width */
    padding: 0.5rem 1rem;
    background-color: rgba(0,0,0,0.4);
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)
st.title("📄 SmartDoc – Document Analyzer")

# =============================
# SESSION STATE
# =============================
if "document_id" not in st.session_state:
    st.session_state.document_id = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =============================
# FILE UPLOAD
# =============================
uploaded_file = st.file_uploader(
    "Upload an invoice or document",
    type=["pdf", "png", "jpg", "jpeg"]
)

# Store file but DO NOT upload automatically
if uploaded_file:
    st.success(f"File selected: {uploaded_file.name}")

    # Add explicit upload + process button
    if st.button("📤 Upload & Process Document"):
        with st.spinner("Uploading..."):
            resp = requests.post(
                f"{API_URL}/process",  # DIRECTLY CALL /process
                files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                timeout=180,
            )
        if not resp.ok:
            st.error(f"Processing failed: {resp.status_code} {resp.text}")
        else:
            data = resp.json()
            st.session_state.document_id = data.get("document", {}).get("id")
            st.session_state.last_result = data


# =============================
# DISPLAY EXTRACTION RESULT
# =============================
res = st.session_state.last_result

if res:
    doc = res.get("document", {})
    latest = res.get("latest_result", {})
    extracted = latest.get("extracted_json", {})

    st.subheader("📋 Extracted Data")
    st.json(extracted)

    st.caption(f"Document ID: {doc.get('id', '—')} • File: {doc.get('filename', '—')}")


# =============================
# 💬 CHAT INTERFACE (RAG + STRUCTURED)
# =============================
st.header("💬 Chat with SmartDoc")

# Persistent state
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{role: "...", content: "..."}]

# Wrapper (prevents layout jumping)
chat_box = st.container()

# Show chat messages
with chat_box:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- Fixed input box anchored at the bottom ---
query = st.chat_input("Ask SmartDoc anything…")

if query:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": query})

    # Re-render messages above
    with chat_box:
        with st.chat_message("user"):
            st.markdown(query)

    # Build payload for backend
    payload = {
        "query": query,
        "top_k": st.session_state.get("top_k", 5),
        "document_ids": [st.session_state.document_id] 
            if st.session_state.document_id else None
    }

    with st.spinner("SmartDoc is thinking…"):
        resp = requests.post(f"{API_URL}/ask", json=payload, timeout=60)
        resp.raise_for_status()
        ans = resp.json()

    # Format SmartDoc reply
    reply_text = f"**{ans.get('answer', '')}**\n\n"
    reply_text += f"*Mode: {ans.get('mode', '').upper()}*"

    # Save the assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply_text})

    # Display the assistant reply
    with chat_box:
        with st.chat_message("assistant"):
            st.markdown(reply_text)

    st.rerun()  # Keeps input at bottom, refreshes cleanly

# =============================
# SIDEBAR: DOCUMENT LIST + DELETE
# =============================

with st.sidebar:
    st.header("Recent Documents")

    delete_footer = st.empty()   # <--- RESERVED FOOTER SLOT

    try:
        # Load recent documents
        r = requests.get(f"{API_URL}/results?limit=20", timeout=20)
        r.raise_for_status()
        rows = r.json()

        if rows:
            # Render the scrollable part of the sidebar
            for i, row in enumerate(rows):
                doc_id = row.get("document_id")
                vendor = (row.get("vendor") or "Unknown Vendor").strip()

                with st.container():
                    col1, col2 = st.columns([3, 1])

                    # Open button
                    with col1:
                        display_vendor = vendor[:25] + "..." if len(vendor) > 25 else vendor
                        if st.button(
                            f"📄 {display_vendor}",
                            key=f"open-{doc_id}",
                            use_container_width=True
                        ):
                            doc_resp = requests.get(f"{API_URL}/results/{doc_id}", timeout=20)
                            if doc_resp.ok:
                                st.session_state.last_result = doc_resp.json()
                                st.rerun()

                    # Trash button
                    with col2:
                        if st.button("🗑️", key=f"del-{doc_id}"):
                            st.session_state["pending_delete"] = {
                                "id": doc_id,
                                "vendor": vendor
                            }
                            st.rerun()

                # Divider between list items
                if i < len(rows) - 1:
                    st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>",
                                unsafe_allow_html=True)

        else:
            st.info("No recent documents")

    except Exception as e:
        st.error(f"Sidebar error: {e}")

    # ---------------------------------------------------------
    # STATIC FOOTER (Delete confirmation stays here)
    # ---------------------------------------------------------
    if st.session_state.get("pending_delete"):
        pd = st.session_state["pending_delete"]

        with delete_footer.container():   # <-- fixed bottom location
            st.markdown("---")
            st.error(f"Delete **{pd['vendor']}** document?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✓ Delete", key="confirm_delete", use_container_width=True):
                    try:
                        delete_resp = requests.delete(
                            f"{API_URL}/documents/{pd['id']}",
                            timeout=20
                        )
                        if delete_resp.ok:
                            # Remove if currently displayed
                            if (st.session_state.get("last_result") and
                                st.session_state["last_result"].get("document", {}).get("id") == pd["id"]):
                                st.session_state["last_result"] = None

                            st.success("Deleted")
                        else:
                            st.error(f"Delete failed: {delete_resp.status_code}")
                    except Exception as exc:
                        st.error(f"Delete error: {exc}")

                    st.session_state.pop("pending_delete", None)
                    st.rerun()

            with col2:
                if st.button("✗ Cancel", key="cancel_delete", use_container_width=True):
                    st.session_state.pop("pending_delete", None)
                    st.rerun()
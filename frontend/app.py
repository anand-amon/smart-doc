import streamlit as st
import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="SmartDoc – Document Analyzer", page_icon="📄")
st.title("📄 SmartDoc – Document Analyzer")

# Keep state
if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

uploaded_file = st.file_uploader(
    "Upload an invoice or document",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file:
    st.success(f"File selected: {uploaded_file.name}")

    # 1) Upload (optional parity with backend)
    with st.spinner("Uploading..."):
        resp = requests.post(
            f"{API_URL}/upload",
            files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
            timeout=120,
        )
    if not resp.ok:
        st.error(f"Upload failed: {resp.status_code} {resp.text}")
        st.stop()

    # 2) Process
    if st.button("🔍 Process Document"):
        with st.spinner("Analyzing document…"):
            uploaded_file.seek(0)  # important
            resp = requests.post(
                f"{API_URL}/process",
                files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                timeout=180,
            )
        if not resp.ok:
            st.error(f"Processing failed: {resp.status_code} {resp.text}")
            st.stop()

        data = resp.json()
        st.session_state.document_id = data.get("document", {}).get("id")
        st.session_state.last_result = data

# ---- Display result (no metrics) ----
res = st.session_state.last_result
if res:
    doc = res.get("document", {}) or {}
    latest = res.get("latest_result", {}) or {}
    extracted = latest.get("extracted_json", {}) or {}

    st.subheader("📋 Extracted Data")
    st.json(extracted)

    st.caption(f"Document ID: {doc.get('id', '—')} • File: {doc.get('filename', '—')}")


# ---- Sidebar: recent documents ----
with st.sidebar:
    st.header("Recent Documents")
    
    try:
        # Get recent results with vendor info
        r = requests.get(f"{API_URL}/results?limit=20", timeout=20)
        r.raise_for_status()
        rows = r.json()

        if rows:
            for i, row in enumerate(rows):
                doc_id = row.get("document_id")
                vendor = (row.get("vendor") or "Unknown Vendor").strip()
                created_at = row.get("created_at", "")
                
                # Create a container for each document
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Make the vendor name clickable to open the document
                        # Truncate if too long
                        display_vendor = vendor[:25] + "..." if len(vendor) > 25 else vendor
                        if st.button(f"📄 {display_vendor}", key=f"open-{doc_id}", 
                                   use_container_width=True,
                                   help=f"Document ID: {doc_id[:8]}..."):
                            doc_resp = requests.get(f"{API_URL}/results/{doc_id}", timeout=20)
                            if doc_resp.ok:
                                st.session_state.last_result = doc_resp.json()
                                st.rerun()
                            else:
                                st.error(f"Failed to load document")
                    
                    with col2:
                        if st.button("🗑️", key=f"del-{doc_id}", 
                                   help="Delete document"):
                            # Store doc to delete in session state
                            st.session_state["pending_delete"] = {
                                "id": doc_id,
                                "vendor": vendor
                            }
                            st.rerun()
                
                # Add subtle separator between documents
                if i < len(rows) - 1:
                    st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.2;'>", 
                              unsafe_allow_html=True)
            
            # Handle delete confirmation at the bottom
            if st.session_state.get("pending_delete"):
                pd = st.session_state["pending_delete"]
                st.markdown("---")
                st.error(f"Delete {pd['vendor']} document?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Delete", type="primary", key="confirm_delete",
                               use_container_width=True):
                        # Use the correct endpoint
                        delete_resp = requests.delete(
                            f"{API_URL}/documents/{pd['id']}", 
                            timeout=20
                        )
                        if delete_resp.ok:
                            # Clear the last result if it's the deleted doc
                            if (st.session_state.get("last_result") and
                                st.session_state.get("last_result", {}).get("document", {}).get("id") == pd['id']):
                                st.session_state["last_result"] = None
                            st.session_state.pop("pending_delete", None)
                            st.success("Document deleted")
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {delete_resp.status_code}")
                            st.session_state.pop("pending_delete", None)
                with col2:
                    if st.button("✗ Cancel", key="cancel_delete",
                               use_container_width=True):
                        st.session_state.pop("pending_delete", None)
                        st.rerun()
        else:
            st.info("No recent documents")
                    
    except requests.exceptions.RequestException as e:
        st.error(f"Could not load recent documents: {e}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

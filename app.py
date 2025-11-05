"""
Streamlit UI for OpenAI RAG Q&A System

streamlit run app.py

A simple web interface for querying your document collection using RAG.
"""

import streamlit as st
from chroma_vector_store import query_with_context, get_collection_info
from dotenv import load_dotenv
import csv
from pathlib import Path

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RAG Q&A System",
    page_icon="🔍",
    layout="centered"
)

# Title and description
st.title("🔍 RAG Q&A System")
st.markdown("Ask questions about your documents and get AI-powered answers.")

# Sidebar with system info
with st.sidebar:
    st.header("System Info")

    # Try to get collection info
    try:
        info = get_collection_info()
        st.success("Connected to ChromaDB")

        # Count source documents
        from pathlib import Path
        docs_dir = Path("docs")
        source_doc_count = len([f for f in docs_dir.iterdir() if f.is_file()])

        st.metric("Source Documents", source_doc_count)
        st.caption(f"{info.get('count', 'N/A')} chunks indexed")
        db_connected = True
    except Exception as e:
        st.error("ChromaDB not found")
        st.caption("Run `python Unstructured_data_pipeline.py` to process documents first.")
        db_connected = False

    st.divider()

    # Instructions
    st.header("How to Use")
    st.markdown("""
    1. Type your question in the text box
    2. Click "Search" or press Enter
    3. Get an AI-generated answer based on your documents

    **Tips:**
    - Be specific in your questions
    - Ask about topics covered in your documents
    - Response time is typically < 3 seconds
    """)

# Main interface
st.divider()

# Mode selection
mode = st.radio("Mode:", ["Single Query", "Batch Queries"], horizontal=True, label_visibility="collapsed")

if mode == "Single Query":
    # Question input
    question = st.text_input(
        "Ask a question:",
        placeholder="e.g., What is the operating temperature range?",
        help="Enter your question about the documents"
    )

    # Search button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
else:
    # Batch mode
    st.markdown("**Upload a text file with questions (one per line):**")
    uploaded_file = st.file_uploader("Choose a .txt file", type=['txt'])

    if uploaded_file is not None:
        questions = uploaded_file.read().decode('utf-8').strip().split('\n')
        questions = [q.strip() for q in questions if q.strip()]

        st.info(f"📋 Found {len(questions)} questions")

        if st.button("▶️ Run Batch Query", type="primary"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, q in enumerate(questions):
                status_text.text(f"Processing question {i+1}/{len(questions)}...")
                try:
                    answer, latency = query_with_context(q)
                    results.append({"question": q, "answer": answer, "latency": latency})
                except Exception as e:
                    results.append({"question": q, "answer": f"ERROR: {str(e)}", "latency": 0})
                progress_bar.progress((i + 1) / len(questions))

            status_text.text("✅ Complete!")

            # Save to CSV
            output_file = "streamlit_batch_results.csv"
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["question", "answer", "latency"])
                writer.writeheader()
                writer.writerows(results)

            st.success(f"✅ Results saved to `{output_file}`")

            # Show results
            for i, r in enumerate(results, 1):
                with st.expander(f"Q{i}: {r['question'][:60]}..."):
                    st.write(f"**Answer:** {r['answer']}")
                    st.caption(f"Latency: {r['latency']:.2f}s")

    search_button = False
    clear_button = False
    question = ""

# Clear functionality
if clear_button:
    st.rerun()

# Process query
if search_button or (question and st.session_state.get('auto_search', False)):
    if not question:
        st.warning("Please enter a question.")
    elif not db_connected:
        st.error("Cannot query: ChromaDB not found. Run the data pipeline first.")
    else:
        try:
            # Query the RAG system (latency is measured internally)
            answer, latency = query_with_context(question)

            # Show answer in a nice box
            st.markdown("### 💡 Answer")
            st.info(answer)

            # Show latency metric
            st.metric("Response Time", f"{latency:.2f}s")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.caption("Make sure you've run the data pipeline and have documents in ChromaDB.")

# Session state for query history (optional future feature)
if 'history' not in st.session_state:
    st.session_state.history = []

# Footer
st.divider()
st.caption("Powered by OpenAI GPT-4, ChromaDB, and Streamlit")

"""
Document Import Utility

Handles uploading, duplicate checking, and processing of new documents.
"""

import hashlib
from pathlib import Path
from typing import Optional, Tuple
from Unstructured_data_pipeline import process_doc_to_json, OUTPUT_DIR
from chroma_vector_store import create_vector_store


def check_duplicate(file_bytes: bytes, docs_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Check if uploaded file is a duplicate based on MD5 hash.

    Args:
        file_bytes: Raw bytes of the uploaded file
        docs_dir: Path to the docs directory

    Returns:
        Tuple of (is_duplicate, matching_filename)
    """
    file_hash = hashlib.md5(file_bytes).hexdigest()

    for existing_file in docs_dir.iterdir():
        if existing_file.is_file():
            with open(existing_file, 'rb') as f:
                existing_hash = hashlib.md5(f.read()).hexdigest()
                if existing_hash == file_hash:
                    return True, existing_file.name

    return False, None


def import_and_process_document(file_bytes: bytes, filename: str, docs_dir: Path = Path("docs")) -> dict:
    """
    Import a document, save it to docs folder, process it, and update vector store.

    Args:
        file_bytes: Raw bytes of the uploaded file
        filename: Name of the file
        docs_dir: Directory to save the document (default: "docs")

    Returns:
        Dictionary with status and message:
        {
            "success": bool,
            "message": str,
            "stage": str  # "duplicate_check", "save", "process", "vector_store"
        }
    """
    try:
        # Check for duplicates
        is_duplicate, matching_file = check_duplicate(file_bytes, docs_dir)
        if is_duplicate:
            return {
                "success": False,
                "message": f"Duplicate detected: '{filename}' matches '{matching_file}'",
                "stage": "duplicate_check"
            }

        # Save to docs folder
        docs_dir.mkdir(exist_ok=True)
        target_path = docs_dir / filename

        with open(target_path, 'wb') as f:
            f.write(file_bytes)

        # Process the document
        OUTPUT_DIR.mkdir(exist_ok=True)
        out_file = OUTPUT_DIR / f"{filename}.jsonl"
        process_doc_to_json(target_path, out_file)

        # Rebuild vector store
        create_vector_store()

        return {
            "success": True,
            "message": f"Successfully imported and processed '{filename}'",
            "stage": "complete"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "stage": "error"
        }

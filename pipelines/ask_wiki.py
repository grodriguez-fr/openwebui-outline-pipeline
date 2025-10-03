import requests
import os

OUTLINE_API_BASE = os.getenv("OUTLINE_API_BASE")
OUTLINE_API_TOKEN = os.getenv("OUTLINE_API_TOKEN")

def _headers():
    return {"Authorization": f"Bearer {OUTLINE_API_TOKEN}"}

def ask_wiki(query: str) -> str:
    """
    Answer a natural language question by navigating Outline (wiki).
    Steps:
      1. Get collections
      2. Identify relevant collections
      3. List documents from those collections
      4. Retrieve content of matching documents
      5. Return a synthesized answer
    """
    try:
        # Step 1: get collections
        url_col = f"{OUTLINE_API_BASE}/collections.list"
        r = requests.post(url_col, headers=_headers())
        r.raise_for_status()
        collections = r.json().get("data", [])

        # Step 2: filter relevant collections
        target_colls = [
            c for c in collections if query.lower() in c.get("name", "").lower()
        ]
        if not target_colls:
            target_colls = collections

        response_parts = []

        # Step 3 & 4: loop through collections and documents
        for coll in target_colls[:3]:  # limit to 3 collections
            col_name = coll.get("name", "[No name]")
            col_id = coll.get("id", "?")

            url_docs = f"{OUTLINE_API_BASE}/collections.documents"
            r2 = requests.post(url_docs, headers=_headers(), json={"id": col_id})
            r2.raise_for_status()
            docs = r2.json().get("data", [])

            matching_docs = [
                d for d in docs if query.lower() in d.get("title", "").lower()
            ] or docs[:3]

            for doc in matching_docs:
                doc_id = doc.get("id")
                doc_title = doc.get("title", "[Untitled]")

                # Step 5: get document content
                url_info = f"{OUTLINE_API_BASE}/documents.info"
                r3 = requests.post(url_info, headers=_headers(), json={"id": doc_id})
                r3.raise_for_status()
                doc_data = r3.json().get("data", {})

                text = doc_data.get("text", "[empty]")[:600]  # truncate
                response_parts.append(f"### {doc_title}\n{text}...\n")

        return (
            f"📚 Results for query: *{query}*\n\n" +
            "\n".join(response_parts)
            if response_parts
            else f"No documents found for '{query}'."
        )

    except Exception as e:
        return f"Error while querying wiki: {e}"

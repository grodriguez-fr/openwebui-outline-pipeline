"""
title: Ask Wiki
author: JECT
date: 2025-10-03
version: 1.0
license: MIT
description: A pipeline to query Outline (wiki) and retrieve answers from collections and documents.
requirements: requests
"""

import os
import requests
from typing import List, Union, Generator, Iterator


class Pipeline:
    def __init__(self):
        self.api_base = None
        self.api_token = None

    async def on_startup(self):
        # Called when pipeline starts
        self.api_base = os.getenv("OUTLINE_API_BASE", "https://wiki.ject.fr/api")
        self.api_token = os.getenv("OUTLINE_API_TOKEN", "")

    async def on_shutdown(self):
        # Called when pipeline stops
        self.api_base = None
        self.api_token = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_token}"}

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipeline logic:
          1. Fetch collections
          2. Identify relevant collections
          3. List documents in them
          4. Retrieve document content
          5. Return excerpts as an answer
        """

        try:
            # Step 1: get collections
            url_col = f"{self.api_base}/collections.list"
            r = requests.post(url_col, headers=self._headers())
            r.raise_for_status()
            collections = r.json().get("data", [])

            # Step 2: filter collections
            query = user_message
            target_colls = [
                c for c in collections if query.lower() in c.get("name", "").lower()
            ]
            if not target_colls:
                target_colls = collections

            response_parts = []

            # Step 3 & 4: documents in collections
            for coll in target_colls[:3]:
                col_id = coll.get("id", "?")
                url_docs = f"{self.api_base}/collections.documents"
                r2 = requests.post(url_docs, headers=self._headers(), json={"id": col_id})
                r2.raise_for_status()
                docs = r2.json().get("data", [])

                matching_docs = [
                    d for d in docs if query.lower() in d.get("title", "").lower()
                ] or docs[:3]

                for doc in matching_docs:
                    doc_id = doc.get("id")
                    doc_title = doc.get("title", "[Untitled]")

                    # Step 5: get content
                    url_info = f"{self.api_base}/documents.info"
                    r3 = requests.post(url_info, headers=self._headers(), json={"id": doc_id})
                    r3.raise_for_status()
                    doc_data = r3.json().get("data", {})

                    text = doc_data.get("text", "[empty]")[:600]
                    response_parts.append(f"### {doc_title}\n{text}...\n")

            return (
                f"📚 Results for query: *{query}*\n\n" + "\n".join(response_parts)
                if response_parts
                else f"No documents found for '{query}'."
            )

        except Exception as e:
            return f"Error while querying wiki: {e}"

"""
title: Outline Wiki Retrieval
author: JECT
date: 2025-10-03
version: 1.0
license: MIT
description: A pipeline to query an Outline wiki (e.g., wiki.ject.fr) and return relevant documents.
requirements: requests
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
import requests
import os
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("DEBUG")


class Pipeline:
    class Valves(BaseModel):
        OUTLINE_API_BASE: str = Field(
            default=os.getenv("OUTLINE_API_BASE", "https://wiki.ject.fr/api"),
            description="Base URL for Outline API",
        )
        OUTLINE_API_TOKEN: str = Field(
            default=os.getenv("OUTLINE_API_TOKEN", ""),
            description="API token for Outline",
        )
        # Removed WORD_LIMIT to return full Markdown content

    def __init__(self):
        self.name = "Outline Wiki Pipeline"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

    async def on_startup(self):
        logger.debug(f"on_startup:{self.name}")

    async def on_shutdown(self):
        logger.debug(f"on_shutdown:{self.name}")

    def _headers(self):
        return {"Authorization": f"Bearer {self.valves.OUTLINE_API_TOKEN}"}

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipeline logic: search for documents in Outline by query and return full Markdown content.
        """
        logger.info(f"User Message: {user_message}")
        streaming = body.get("stream", False)
        context = ""

        try:
            # 1. Search documents in Outline
            r = requests.post(
                f"{self.valves.OUTLINE_API_BASE}/documents.search",
                headers=self._headers(),
                json={
                    "query": user_message,
                    "includeArchived": False
                },
            )

            r.raise_for_status()
            docs = r.json().get("data", [])

            if not docs:
                return f"No documents found for '{user_message}'"

            multi_part = False
            for doc in docs[:3]:  # limit to 3 docs
                if multi_part and streaming:
                    yield "---\n"

                doc_id = doc.get("document", {}).get("id")
                doc_title = doc.get("document", {}).get("title", "[Untitled]")

                # 2. Get document content (Markdown)
                r = requests.post(
                    f"{self.valves.OUTLINE_API_BASE}/documents.info",
                    headers=self._headers(),
                    json={"id": doc_id},
                )
                r.raise_for_status()
                doc_data = r.json().get("data", {})
                # Outline returns Markdown in the 'text' field
                markdown_text = doc_data.get("text", "[empty]")

                chunk = f"## {doc_title}\n\n{markdown_text}\n"

                if streaming:
                    yield chunk
                else:
                    context += chunk + "\n"

                multi_part = True

            if not streaming:
                return context if context else "No relevant content"

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return f"Error while querying Outline: {e}"

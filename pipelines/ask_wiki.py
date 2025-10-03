"""
title: Outline Wiki Retrieval
author: JECT
date: 2025-10-03
version: 1.0
license: MIT
description: A pipeline to query an Outline wiki (e.g., wiki.ject.fr) and return relevant documents.
requirements: requests
"""

from typing import List, Union, Iterator
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

    def __init__(self):
        self.name = "Outline Wiki Pipeline"
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )

    async def on_startup(self):
        logger.debug(f"on_startup:{self.name}")

    async def on_shutdown(self):
        logger.debug(f"on_shutdown:{self.name}")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.valves.OUTLINE_API_TOKEN}"}

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> Union[str, Iterator[str]]:
        """
        Main pipeline logic: search for documents in Outline by query and return content.
        - If streaming: yield Markdown chunks as they are retrieved.
        - If not streaming: accumulate results and return a prompt asking the LLM to answer the user question.
        """
        logger.info(f"User Message: {user_message}")
        streaming = body.get("stream", False)

        # Validate token early
        if not self.valves.OUTLINE_API_TOKEN:
            return "Outline API token is missing. Please set OUTLINE_API_TOKEN."

        def generate() -> Iterator[str]:
            try:
                # 1. Search documents in Outline
                r = requests.post(
                    f"{self.valves.OUTLINE_API_BASE}/documents.search",
                    headers=self._headers(),
                    json={"query": user_message, "includeArchived": False},
                    timeout=15,
                )
                r.raise_for_status()
                docs = r.json().get("data", [])

                if not docs:
                    yield f"No documents found for '{user_message}'"
                    return

                multi_part = False
                for doc in docs[:3]:  # limit to 3 docs
                    if multi_part:
                        yield "---\n"

                    doc_id = doc.get("document", {}).get("id")
                    doc_title = doc.get("document", {}).get("title", "[Untitled]")

                    # 2. Get document content
                    r_info = requests.post(
                        f"{self.valves.OUTLINE_API_BASE}/documents.info",
                        headers=self._headers(),
                        json={"id": doc_id},
                        timeout=15,
                    )
                    r_info.raise_for_status()
                    doc_data = r_info.json().get("data", {})
                    markdown_text = doc_data.get("text", "[empty]")

                    yield f"## {doc_title}\n\n{markdown_text}\n"
                    multi_part = True

            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                yield f"Error while querying Outline: {e}"

        if streaming:
            # mode streaming -> renvoie le générateur tel quel
            return generate()
        else:
            # mode non-streaming -> accumule et contextualise
            context = "".join(generate())
            if context.strip():
                return (
                    f"The following information was retrieved from the Outline wiki:\n\n"
                    f"{context}\n\n"
                    f"Using this information, please answer the question:\n"
                    f"{user_message}"
                )
            else:
                return "No relevant content"

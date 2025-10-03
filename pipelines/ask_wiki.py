"""
title: Outline Wiki Retrieval
author: JECT
date: 2025-10-03
version: 1.0
license: MIT
description: A pipeline pour interroger le wiki Outline (wiki.ject.fr) et récupérer des documents pertinents.
requirements: requests, pydantic
"""

import os
import requests
from typing import Iterator, Union, List
from pydantic import BaseModel, Field
from logging import getLogger

from pipelines import Pipeline, Message

logger = getLogger(__name__)
logger.setLevel("DEBUG")


# -------------------------------------------------------------------------
# Tools encapsulant l’API Outline
# -------------------------------------------------------------------------
class OutlineTools:
    class Valves(BaseModel):
        outline_api_base: str = Field(
            default=os.getenv("OUTLINE_API_BASE", "https://wiki.ject.fr/api"),
            description="URL de base de l'API Outline",
        )
        outline_api_token: str = Field(
            default=os.getenv("OUTLINE_API_TOKEN", ""),
            description="Token API Outline",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self):
        return {"Authorization": f"Bearer {self.valves.outline_api_token}"}

    def list_collections(self) -> str:
        url = f"{self.valves.outline_api_base}/collections.list"
        try:
            r = requests.post(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            return "\n".join(
                [f"{c.get('name','[Sans nom]')} (id={c.get('id')})" for c in data.get("data", [])]
            ) or "Aucune collection trouvée."
        except Exception as e:
            return f"Erreur list_collections: {e}"

    def list_collection_docs(self, collection_id: str) -> str:
        url = f"{self.valves.outline_api_base}/collections.documents"
        try:
            r = requests.post(url, headers=self._headers(), json={"id": collection_id})
            r.raise_for_status()
            data = r.json()
            return "\n".join(
                [f"{d.get('title','[Sans titre]')} (id={d.get('id')})" for d in data.get("data", [])][:20]
            ) or f"Aucun document trouvé dans {collection_id}."
        except Exception as e:
            return f"Erreur list_collection_docs: {e}"

    def search_docs(self, query: str) -> str:
        url = f"{self.valves.outline_api_base}/documents.search"
        try:
            r = requests.post(url, headers=self._headers(), json={"query": query})
            r.raise_for_status()
            data = r.json()
            return "\n".join(
                [f"{d.get('document',{}).get('title','[Sans titre]')} (id={d.get('document',{}).get('id')})"
                 for d in data.get("data", [])][:5]
            ) or "Aucun résultat."
        except Exception as e:
            return f"Erreur search_docs: {e}"

    def get_doc(self, doc_id: str) -> str:
        url = f"{self.valves.outline_api_base}/documents.info"
        try:
            r = requests.post(url, headers=self._headers(), json={"id": doc_id})
            r.raise_for_status()
            data = r.json()
            title = data.get("data", {}).get("title", "Sans titre")
            text = data.get("data", {}).get("text", "[vide]")
            return f"# {title}\n\n{text[:1000]}..."
        except Exception as e:
            return f"Erreur get_doc: {e}"


# -------------------------------------------------------------------------
# Pipeline OpenWebUI
# -------------------------------------------------------------------------
class OutlineWikiPipeline(Pipeline):
    class Valves(BaseModel):
        OUTLINE_API_BASE: str = Field(
            default=os.getenv("OUTLINE_API_BASE", "https://wiki.ject.fr/api"),
            description="Base URL de l’API Outline",
        )
        OUTLINE_API_TOKEN: str = Field(
            default=os.getenv("OUTLINE_API_TOKEN", ""),
            description="Clé API Outline",
        )

    def __init__(self):
        super().__init__()
        self.name = "Outline Wiki Pipeline"
        self.valves = self.Valves()
        self.tools = OutlineTools()

    def on_startup(self, ctx):
        logger.info("✅ OutlineWikiPipeline initialisée avec %s", self.valves.OUTLINE_API_BASE)

    def on_shutdown(self, ctx):
        logger.info("🛑 OutlineWikiPipeline arrêtée")

    def invoke(self, messages: List[Message], stream: bool = False) -> Union[Iterator[Message], Message]:
        last = messages[-1]
        text = last.content.strip()

        logger.debug("➡️ Reçu: %s", text)

        if text.startswith("/collections"):
            result = self.tools.list_collections()
        elif text.startswith("/docs "):
            collection_id = text.split(" ", 1)[1]
            result = self.tools.list_collection_docs(collection_id)
        elif text.startswith("/search "):
            query = text.split(" ", 1)[1]
            result = self.tools.search_docs(query)
        elif text.startswith("/get "):
            doc_id = text.split(" ", 1)[1]
            result = self.tools.get_doc(doc_id)
        else:
            result = (
                "❓ Commandes disponibles:\n"
                "/collections → Liste les collections\n"
                "/docs <collection_id> → Liste les docs d’une collection\n"
                "/search <mot-clé> → Recherche de documents\n"
                "/get <doc_id> → Récupère le contenu d’un document"
            )

        return Message(role="assistant", content=result)

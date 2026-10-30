"""A lexical tool shortlist, used while the embedding service is unreachable.

Tools are ranked with BM25 over their names, descriptions and parameter names: words shared with
the question count more when they are rare across the catalog, and long descriptions do not win
just by mentioning more words. Common words weigh almost nothing, so no stop-word list is needed.
The shortlist is then expanded with the producers of every key the shortlisted tools require, so a
chain can always be completed from it.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from aria.catalog.catalog import ToolCatalog
from aria.catalog.validation import CatalogTool


def words(text: str) -> list[str]:
    # Split camelCase tool and parameter names into their words as well.
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return [_stem(word) for word in re.findall(r"[a-z0-9]+", spaced.lower())]


def _stem(word: str) -> str:
    # Plurals only; enough to match "divisions" to "division" and "codes" to "code".
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "xes", "ches", "shes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


# BM25 parameters: term-frequency saturation and length normalisation, at their usual values.
BM25_K1 = 1.2
BM25_B = 0.75
# A tool's name says what it does more reliably than its description, so its words count double.
NAME_WEIGHT = 2


def tool_document(tool: CatalogTool) -> list[str]:
    parameters = " ".join(parameter.name for parameter in tool.declaration.parameters)
    return words(tool.name) * NAME_WEIGHT + words(f"{tool.description} {parameters}")


def shortlist(question: str, catalog: ToolCatalog, k: int) -> list[str]:
    documents = {name: tool_document(tool) for name, tool in catalog.tools.items()}
    if not documents:
        return []
    frequencies = {name: Counter(document) for name, document in documents.items()}
    document_frequency = Counter(word for counts in frequencies.values() for word in counts)
    total = len(documents)
    average_length = sum(len(document) for document in documents.values()) / total
    query = set(words(question))

    def score(name: str) -> float:
        counts = frequencies[name]
        length_factor = 1 - BM25_B + BM25_B * len(documents[name]) / average_length
        result = 0.0
        for word in query & counts.keys():
            rarity = math.log(1 + (total - document_frequency[word] + 0.5) / (document_frequency[word] + 0.5))
            result += rarity * counts[word] * (BM25_K1 + 1) / (counts[word] + BM25_K1 * length_factor)
        return result

    scores = {name: score(name) for name in documents}
    ranked = sorted((name for name in documents if scores[name] > 0), key=lambda name: (-scores[name], name))
    return expand_with_producers(ranked[:k], catalog)


def expand_with_producers(names: list[str], catalog: ToolCatalog) -> list[str]:
    """Add the tools that produce keys the shortlisted tools require, recursively."""
    result = list(names)
    queue = list(names)
    while queue:
        tool = catalog.tools[queue.pop(0)]
        for key_id in tool.required_keys:
            for producer in catalog.graph.producers_of(key_id):
                if producer not in result:
                    result.append(producer)
                    queue.append(producer)
    return result

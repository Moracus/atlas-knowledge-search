# app/llm/prompts.py

from app.llm.base import Message, Role
from app.services.chunking.base import ChunkData


SYSTEM_PROMPT = """\
You are Atlas, a codebase question-answering assistant.

Rules:
- Answer ONLY using the provided context.
- Do not invent APIs, functions, or files.
- If the answer is not present in the context, say so clearly.
- When making a claim, cite the relevant source using its number like [1] or [2].
- Keep answers concise and technical.
"""


def build_messages(
    question: str,
    chunks: list[ChunkData],
) -> list[Message]:
    """Construct chat messages from retrieved chunks."""

    context_blocks = []

    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"""[{idx}]
File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}

{chunk.text}"""
        )

    user_prompt = f"""\
Context:

{chr(10).join(context_blocks)}

Question:
{question}
"""

    return [
        Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        Message(role=Role.USER, content=user_prompt),
    ]
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_python as tspython

from app.services.chunking.base import BaseChunker, ChunkData


PY_LANGUAGE = Language(tspython.language())


class PythonChunker(BaseChunker):
    def __init__(self):
        self.parser = Parser(PY_LANGUAGE)

    def chunk(self, text: str, file_path: str) -> list[ChunkData]:
        tree = self.parser.parse(text.encode("utf-8"))
        root = tree.root_node

        lines = text.splitlines()
        language = self.detect_language(file_path)
        file_name = Path(file_path).name

        chunks: list[ChunkData] = []

        for node in root.children:
            if node.type in ("import_statement", "import_from_statement"):
                chunks.append(
                    self._build_chunk(
                        node=node,
                        text=text,
                        lines=lines,
                        file_path=file_path,
                        file_name=file_name,
                        language=language,
                        chunk_type="import",
                        name=None,
                    )
                )

            elif node.type == "function_definition":
                name = self._identifier(node, text)
                chunks.append(
                    self._build_chunk(
                        node=node,
                        text=text,
                        lines=lines,
                        file_path=file_path,
                        file_name=file_name,
                        language=language,
                        chunk_type="function",
                        name=name,
                    )
                )

            elif node.type == "class_definition":
                class_name = self._identifier(node, text)

                chunks.append(
                    self._build_chunk(
                        node=node,
                        text=text,
                        lines=lines,
                        file_path=file_path,
                        file_name=file_name,
                        language=language,
                        chunk_type="class",
                        name=class_name,
                    )
                )

                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "function_definition":
                            method = self._identifier(child, text)

                            chunks.append(
                                self._build_chunk(
                                    node=child,
                                    text=text,
                                    lines=lines,
                                    file_path=file_path,
                                    file_name=file_name,
                                    language=language,
                                    chunk_type="method",
                                    name=f"{class_name}.{method}",
                                )
                            )

        return chunks

    def _build_chunk(
        self,
        *,
        node,
        text: str,
        lines: list[str],
        file_path: str,
        file_name: str,
        language: str,
        chunk_type: str,
        name: str | None,
    ) -> ChunkData:
        start = node.start_point[0] + 1
        end = node.end_point[0] + 1

        snippet = "\n".join(lines[start - 1 : end])

        return ChunkData(
            text=snippet,
            file_path=file_path,
            file_name=file_name,
            language=language,
            chunk_type=chunk_type,
            name=name,
            start_line=start,
            end_line=end,
        )

    def _identifier(self, node, source: str) -> str | None:
        ident = node.child_by_field_name("name")
        if ident is None:
            return None

        return source[ident.start_byte : ident.end_byte]
from typing import List
import re


def split_text(text: str, max_chars_per_chunk: int = 2500, overwrap: int = 500) -> List[str]:
    if text is None:
        raise ValueError("text must not be None")
    if max_chars_per_chunk <= 0:
        raise ValueError("max_chars_per_chunk must be greater than 0")
    if max_chars_per_chunk <= overwrap:
        raise ValueError("max_chars_per_chunk must be greater than overwrap")

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars_per_chunk

        if end < len(text):
            newline_position = text.rfind('\n', end - overwrap, end)
            if newline_position != -1:
                end = newline_position + 1
            else:
                end = start + max_chars_per_chunk

        chunks.append(text[start:end])
        start = end

    return chunks


def split_md_text(text: str, max_chars_per_chunk: int = 2500) -> List[str]:
    if text is None:
        raise ValueError("text must not be None")
    if max_chars_per_chunk <= 0:
        raise ValueError("max_chars_per_chunk must be greater than 0")

    if not text:
        return []

    # Check if the "## References" header exists
    reference_index = text.find('## References')
    reference_chunk = None
    if reference_index != -1:
        # If the header exists, split the text into the part before and after the header
        reference_chunk = text[reference_index:]
        text = text[:reference_index]

    # Split the text into chunks by mathematical formulas and tables
    chunks = re.split(r'(\$\$.*?\$\$|(?:^\|.*?\|$)(?:\n^\|.*?\|$)*)',
                      text, flags=re.DOTALL | re.MULTILINE)
    chunks = [chunk for chunk in chunks if chunk.strip()]

    # Further split the non-formula and non-table chunks if they are too long
    final_chunks = []
    for chunk in chunks:
        # This is a formula or a table, keep it intact
        if (chunk.startswith('$$') and chunk.endswith('$$')) or (chunk.strip().startswith('|') and chunk.strip().endswith('|')):
            final_chunks.append(chunk)
        else:  # This is a non-formula and non-table chunk, split it if it's too long
            while len(chunk) > max_chars_per_chunk:
                split_index = chunk.rfind('\n', 0, max_chars_per_chunk)
                if split_index == -1:  # No newline character found, split at the max_chars_per_chunk
                    split_index = max_chars_per_chunk
                # Add the newline at the end
                final_chunks.append(chunk[:split_index] + '\n')
                # Remove leading whitespaces
                chunk = chunk[split_index:].lstrip()
            final_chunks.append(chunk)

    # Add the reference chunk (if it exists) as a single chunk
    if reference_chunk:
        final_chunks.append(reference_chunk)

    return final_chunks

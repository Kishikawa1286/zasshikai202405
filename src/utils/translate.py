import os
import aiohttp
import json
from typing import List
import asyncio
from tqdm.asyncio import tqdm


def translate_prompt(document: str, correspondence_list: str) -> str:
    return f"""Your task is to translate the given Document into Japanese.
Pay attention to the words in the Word Correspondence List when translating.
Keep names and place names in their original language.
**Do not wrap the translated text in Markdown code blocks.**

## Word Correspondence List
\"\"\"
{correspondence_list}
\"\"\"

## Document
\"\"\"
{document}
\"\"\""""


async def translate(document: str, correspondence_list: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("environment variable OPENAI_API_KEY must be set")

    if document.startswith("$$") or document.startswith("|") or document.startswith("## References"):
        return document

    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": translate_prompt(document, correspondence_list)}],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
                response = await resp.json()

                try:
                    return response['choices'][0]['message']['content']
                except (KeyError, IndexError) as e:
                    print(f"Error occurred. response: {response}")
                    return document

    except aiohttp.ServerDisconnectedError:
        print("Server disconnected. Returning original document.")
        return document


async def translate_chunks(chunks: List[str], correpondence_list: str, batch_size: int = 10, timeout: int = 30000):
    bs = min(batch_size, len(chunks))
    results = []
    # calculate total number of batches
    total_batches = (len(chunks) + bs - 1) // bs
    for i in range(0, len(chunks), bs):
        batch_number = i // bs + 1  # calculate current batch number
        print(f"Processing batch {batch_number} of {total_batches}")
        tasks = [translate(chunk, correpondence_list)
                 for chunk in chunks[i:i+bs]]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(chunk_results)
        # Wait for timeout after each batch, except for the last one
        if i + bs < len(chunks):
            await asyncio.sleep(timeout / 1000)  # timeout is in milliseconds
    return results

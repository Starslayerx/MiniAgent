import asyncio
from pathlib import Path

import aiofiles


async def read_single_file(filepath: Path):
    async with aiofiles.open(filepath, encoding='utf-8') as f:
        return await f.read()


async def get_compress_prompts() -> tuple[str, ...]:
    folder = Path(__file__).parent / 'templates' / 'compress'
    files = [folder / 'summary.md', folder / 'summary_prefix.md']
    tasks = [read_single_file(file) for file in files]
    contents = await asyncio.gather(*tasks)
    results = tuple(contents)
    return results

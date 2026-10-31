"""Worker entrypoint: discovers workflows in src/workflows and starts the worker."""

import asyncio

import mistralai.workflows as mistralai_workflows
from mistralai.workflows import discover_workflows


async def main() -> None:
    discovered = discover_workflows()
    await mistralai_workflows.run_worker(discovered)


if __name__ == "__main__":
    asyncio.run(main())

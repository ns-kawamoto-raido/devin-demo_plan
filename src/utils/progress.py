from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, Iterator, TypeVar

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

T = TypeVar("T")


console = Console()


@contextmanager
def spinner(message: str) -> Iterator[None]:
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task_id = progress.add_task(message, total=None)
        try:
            yield
        finally:
            progress.update(task_id, completed=1)


def track_iter(iterable: Iterable[T], description: str | None = None) -> Iterator[T]:
    desc = description or "Processing"
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(desc, total=None)
        for item in iterable:
            yield item
            progress.advance(task_id)


"""Progress bar utilities using Rich library."""

from typing import Any

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def create_progress_bar() -> Progress:
    """Create a Rich progress bar for file processing.

    Returns:
        Configured Progress instance
    """
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )


def create_spinner() -> Progress:
    """Create a Rich spinner for indeterminate operations.

    Returns:
        Configured Progress instance with spinner
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TimeElapsedColumn(),
    )


class ProgressTracker:
    """Progress tracker for file processing operations."""

    def __init__(self, description: str, total: int | None = None, quiet: bool = False) -> None:
        """Initialize progress tracker.

        Args:
            description: Description of the operation
            total: Total number of items (None for spinner)
            quiet: If True, suppress progress output
        """
        self.description = description
        self.total = total
        self.quiet = quiet
        self.progress: Progress | None = None
        self.task_id: TaskID | None = None

    def __enter__(self) -> "ProgressTracker":
        """Start progress tracking."""
        if not self.quiet:
            if self.total is not None:
                self.progress = create_progress_bar()
            else:
                self.progress = create_spinner()
            self.progress.__enter__()
            self.task_id = self.progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop progress tracking."""
        if self.progress is not None:
            self.progress.__exit__(*args)

    def update(self, advance: int = 1, description: str | None = None) -> None:
        """Update progress.

        Args:
            advance: Number of items to advance
            description: Optional new description
        """
        if self.progress is not None and self.task_id is not None:
            if description is not None:
                self.progress.update(self.task_id, description=description, advance=advance)
            else:
                self.progress.update(self.task_id, advance=advance)

    def set_total(self, total: int) -> None:
        """Set total number of items.

        Args:
            total: Total number of items
        """
        if self.progress is not None and self.task_id is not None:
            self.progress.update(self.task_id, total=total)

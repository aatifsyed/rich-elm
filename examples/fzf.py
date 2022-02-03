from dataclasses import dataclass
from queue import Queue
from signal import SIGWINCH
from typing import Generic, Iterable, List, Optional, Set, TypeVar, Union

from fuzzywuzzy.fuzz import ratio  # type: ignore
from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys
from returns.result import safe
from rich.color import Color
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    OverflowMethod,
    RenderResult,
    RichCast,
)
from rich.style import Style
from rich.table import Table, box
from rich.text import Text
from rich_elm import events
from rich_elm.events import Signal

T = TypeVar("T")


@dataclass
class Select(Generic[T]):
    inner: T
    selected: bool = False


@dataclass
class ListView:
    start: Optional[int]
    end: Optional[int]
    selected: int
    candidates: List[Select[str]]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        pass


@dataclass
class FuzzyState(ConsoleRenderable):
    needle: str
    choices: List[Select[str]]
    index: int

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult":
        yield Text(text=self.needle, overflow="ellipsis")
        for choice in self.choices:
            yield Text(text=choice.inner, overflow="ellipsis")


@safe(exceptions=(KeyboardInterrupt,))  # type: ignore
def fuzzyfinder_safe(candidates: Iterable[str]) -> str:
    queue: "Queue[KeyPress | Signal]" = Queue()
    with Console(stderr=True).screen() as ctx, events.for_signals(
        SIGWINCH, queue=queue
    ), events.for_stdin(queue=queue):
        console: Console = ctx.console
        state = FuzzyState(
            needle="", choices=list(Select(c) for c in candidates), index=0
        )

        console.update_screen(state)  # Initial display

        while event := queue.get():
            if isinstance(event, Signal):
                console.update_screen(state)  # Redraw on resize
            elif isinstance(event.key, Keys):

                # Control character
                raise NotImplementedError(event)
            else:
                state.needle += event.key
                console.update_screen(state)


def fuzzyfinder(candidates: Iterable[str]) -> Optional[str]:
    return fuzzyfinder_safe(candidates).value_or(None)


if __name__ == "__main__":
    print(
        fuzzyfinder(
            [
                "The Zen of Python, by Tim Peters",
                "Beautiful is better than ugly.",
                "Explicit is better than implicit.",
                "Simple is better than complex.",
                "Complex is better than complicated.",
                "Flat is better than nested.",
                "Sparse is better than dense.",
                "Readability counts.",
                "Special cases aren't special enough to break the rules.",
                "Although practicality beats purity.",
                "Errors should never pass silently.",
                "Unless explicitly silenced.",
                "In the face of ambiguity, refuse the temptation to guess.",
                "There should be one-- and preferably only one --obvious way to do it.",
                "Although that way may not be obvious at first unless you're Dutch.",
                "Now is better than never.",
                "Although never is often better than *right* now.",
                "If the implementation is hard to explain, it's a bad idea.",
                "If the implementation is easy to explain, it may be a good idea.",
                "Namespaces are one honking great idea -- let's do more of those!",
            ]
        )
    )

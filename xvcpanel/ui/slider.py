"""Mouse-drag slider for live controls. Textual 8 ships no Slider widget."""

from __future__ import annotations

from rich.text import Text
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget

TRACK_FILLED = "\u258d"
TRACK_EMPTY = "\u258e"


class Slider(Widget):
    """Minimal drag-to-scrub horizontal slider."""

    DEFAULT_CSS = """
    Slider {
        height: 1;
        margin-top: 1;
    }
    Slider:focus {
        outline: none;
        text-style: bold;
    }
    """

    class Changed(Message):
        def __init__(self, slider: "Slider", value: float) -> None:
            super().__init__()
            self.slider = slider
            self.value = value

        @property
        def control(self) -> "Slider":
            return self.slider

    value = reactive(0.5)

    def __init__(
        self,
        minimum: float = 0.0,
        maximum: float = 1.0,
        value: float = 0.5,
        *,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.minimum = minimum
        self.maximum = maximum
        self.value = self._clamp(value)
        self._dragging = False

    def _clamp(self, value: float) -> float:
        return max(min(value, self.maximum), self.minimum)

    def _span(self) -> float:
        span = self.maximum - self.minimum
        return span if span > 0 else 1.0

    def _frac(self) -> float:
        return (self.value - self.minimum) / self._span()

    def _set_from_x(self, x: int) -> None:
        width = max(1, self.size.width - 1)
        frac = max(0.0, min(1.0, x / width))
        value = self.minimum + frac * self._span()
        if value != self.value:
            self.value = value
            self.post_message(self.Changed(self, value))

    def on_mouse_down(self, event) -> None:
        self.capture_mouse()
        self._dragging = True
        self._set_from_x(event.x)
        event.stop()

    def on_mouse_move(self, event) -> None:
        if self._dragging:
            self._set_from_x(event.x)
        event.stop()

    def on_mouse_up(self, event) -> None:
        self._dragging = False
        self.release_mouse()
        event.stop()

    def render(self) -> Text:
        width = max(1, self.size.width - 1)
        fill = round(self._frac() * width)
        text = Text()
        if fill:
            text.append(TRACK_FILLED * fill, style="#00ff9d bold")
        if width - fill:
            text.append(TRACK_EMPTY * (width - fill), style="#262a33")
        return text
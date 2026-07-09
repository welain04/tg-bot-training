from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class TimeInterval:
    start: time
    end: time

    @property
    def start_minutes(self) -> int:
        return self.start.hour * 60 + self.start.minute

    @property
    def end_minutes(self) -> int:
        return self.end.hour * 60 + self.end.minute

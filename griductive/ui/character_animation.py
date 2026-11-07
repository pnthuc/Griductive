"""Public visual state only. No hidden solution, clue or solver access."""
from dataclasses import dataclass


@dataclass
class CharacterAnimation:
    status: str | None = None
    elapsed: float = 0.
    reaction: float = 0.
    arrival: float = 0.

    def advance(self,seconds):
        seconds=max(0.,seconds)
        self.elapsed+=seconds
        self.arrival+=seconds
        self.reaction=max(0.,self.reaction-seconds)

    def react(self):self.reaction=.65

    def set_status(self,status):
        if status not in (None,'INNOCENT','CRIMINAL'):raise ValueError(status)
        if status!=self.status:
            self.status=status;self.arrival=0.;self.react()

    @property
    def frame(self):
        if self.status=='CRIMINAL':
            if self.reaction>.25 or self.arrival<.35:return 5
            return 6
        if self.status=='INNOCENT':
            if self.reaction>0 or self.arrival<.6:return 3
            return 4
        if self.reaction>0:return 2
        return 0

    @property
    def blink_frame(self):return 3 if self.status=='INNOCENT' else 1

    @property
    def blink_amount(self):
        # The prison resting pose already looks down.
        if self.status=='CRIMINAL' or self.reaction>0 or (self.status and self.arrival<.7):return 0.
        phase=self.elapsed%{None:4.1,'INNOCENT':4.3,'CRIMINAL':4.7}[self.status]
        if phase<.09:t=phase/.09
        elif phase<.15:return 1.
        elif phase<.28:t=1-(phase-.15)/.13
        else:return 0.
        return t*t*(3-2*t)

    @property
    def bars_progress(self):return min(1.,self.arrival/.65) if self.status=='CRIMINAL' else 0.

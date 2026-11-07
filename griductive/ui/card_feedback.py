"""Short, interruptible card emphasis driven by the existing UI clock."""
from dataclasses import dataclass
from math import sin, pi


@dataclass
class CardFeedback:
    scale: float = 1.
    opacity: float = 1.
    scale_target: float = 1.
    opacity_target: float = 1.
    scale_start: float = 1.
    opacity_start: float = 1.
    zoom_time: float = .18
    fade_time: float = .18
    pulse_time: float = .38

    def emphasize(self, selected, dimmed, animate):
        scale=1.10 if selected else 1.
        opacity=.28 if dimmed else 1.
        if scale!=self.scale_target:
            self.scale_start=self.scale;self.scale_target=scale;self.zoom_time=0.
        if opacity!=self.opacity_target:
            self.opacity_start=self.opacity;self.opacity_target=opacity;self.fade_time=0.
        if not animate:self.finish()

    def pulse(self, animate):
        self.pulse_time=0. if animate else .38

    def finish(self):
        self.scale=self.scale_target;self.opacity=self.opacity_target
        self.zoom_time=self.fade_time=.18;self.pulse_time=.38

    def advance(self, seconds):
        self.zoom_time=min(.18,self.zoom_time+seconds)
        self.fade_time=min(.18,self.fade_time+seconds)
        self.pulse_time=min(.38,self.pulse_time+seconds)
        zoom=1-(1-self.zoom_time/.18)**3
        fade=1-(1-self.fade_time/.18)**3
        self.scale=self.scale_start+(self.scale_target-self.scale_start)*zoom
        self.opacity=self.opacity_start+(self.opacity_target-self.opacity_start)*fade

    @property
    def pop(self):
        return sin(pi*self.pulse_time/.38)**2 if self.pulse_time<.38 else 0.

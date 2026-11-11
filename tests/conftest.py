from collections.abc import Sequence

from praxiloop.contracts import InvestigationRequest, ModelAction, ToolObservation


class ScriptedModel:
    def __init__(self, actions: Sequence[ModelAction]) -> None:
        self.actions = list(actions)
        self.calls = 0

    async def decide(
        self, request: InvestigationRequest, observations: Sequence[ToolObservation]
    ) -> ModelAction:
        self.calls += 1
        return self.actions[min(self.calls - 1, len(self.actions) - 1)]

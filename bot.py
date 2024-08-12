import random

import library
import state
from simulator import (
    Simulator, ActionBattleApplySide, ActionBattleSaveSide, ActionBattleEndTurn,
    ActionLevelUp,
)


class Bot:
    def __init__(self):
        self.simulator = Simulator()

    def run(self):
        s = self.simulator
        s.set_up({})
        while s.state.phase != state.Phase.FINISHED:
            while s.state.phase not in (state.Phase.LEVEL_UP, state.Phase.FINISHED):
                self._step_battle()
            self._step_level_up()
        return s.state.round

    def _step_battle(self):
        s = self.simulator
        for heroID in s.state.heroes:
            s.apply_actions([ActionBattleSaveSide([heroID])])
        for heroID in s.state.heroes:
            if len(s.state.monsters) != 0:
                sideID = s.state.saved_sides[heroID]
                if isinstance(
                    s.heroesLib.getByName(s.state.heroes[heroID].name).sides[sideID],
                    library.SideSword,
                ):
                    targetID = random.choice(list(s.state.monsters.keys()))
                else:
                    targetID = random.choice(list(s.state.heroes.keys()))
                s.apply_actions([ActionBattleApplySide(heroID, sideID, targetID)])
        s.apply_actions([ActionBattleEndTurn()])

    def _step_level_up(self):
        s = self.simulator
        s.apply_actions([ActionLevelUp()])

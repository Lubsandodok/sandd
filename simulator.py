import abc
import enum
import random
import uuid
from typing import List, Optional, OrderedDict

import library
from state import Phase, SimulatorState, HeroState, MonsterState, HeroID, MonsterID, PositionState, Row


class ActionType(enum.Enum):
    NONE = enum.auto()
    LEVEL_UP = enum.auto()
    ITEM_SELECTION = enum.auto()
    ITEM_DISTRIBUTION = enum.auto()
    BATTLE_SAVE_SIDE = enum.auto()
    BATTLE_APPLY_SIDE = enum.auto()
    BATTLE_REROLL = enum.auto()
    BATTLE_END_TURN = enum.auto()
    BATTLE_UNDO = enum.auto()


class Action(abc.ABC):

    @abc.abstractmethod
    def apply(self):
        pass

    # @abc.abstractmethod
    # def can_apply(self):
    #     pass

    @classmethod
    def check_and_remove_target(cls, state, targetID):
        if targetID in state.monsters:
            monster = state.monsters[targetID]
            if monster.health <= 0:
                state.monsters_position[targetID].dead = True
                del state.monsters[targetID]
                del state.monster_sides[targetID]
        elif targetID in state.heroes:
            hero = state.heroes[targetID]
            if hero.health <= 0:
                state.heroes_position[targetID].dead = True
                del state.heroes[targetID]
                if targetID in state.table_sides:
                    del state.table_sides[targetID]
                if targetID in state.saved_sides:
                    del state.saved_sides[targetID]


class ActionBattleSaveSide(Action):
    def __init__(self, heroes: List[HeroID]):
        self.heroes = heroes

    def apply(self, state) -> library.Result:
        for heroID in self.heroes:
            if heroID in state.table_sides:
                state.saved_sides[heroID] = state.table_sides[heroID]
                del state.table_sides[heroID]
            else:
                pass


class ActionBattleApplySide(Action):
    def __init__(self, heroID, sideID, targetID):
        self.heroID = heroID
        self.sideID = sideID
        self.targetID = targetID

    def apply(self, state):
        hero_state = state.heroes[self.heroID]
        if not library.Character.can_side_be_used(hero_state, self.sideID):
            return library.Result(True)

        # apply side logic
        side_state = hero_state.sides[self.sideID]
        side_cls = library.Side.get_cls(side_state.name)
        side_cls.apply(state, side_state, self.targetID)
        # apply keywords logic
        for k_state in side_state.keywords.values():
            k_cls = library.Keyword.get_cls(k_state.name)
            k_cls.apply(state, side_state, self.heroID, self.targetID)

        # TODO: inefficient
        for heroID in list(state.heroes.keys()):
            Action.check_and_remove_target(state, heroID)
        for monsterID in list(state.monsters.keys()):
            Action.check_and_remove_target(state, monsterID)
        # Action.check_and_remove_target(state, self.heroID)
        # Action.check_and_remove_target(state, self.targetID)

        return library.Result(True)


class ActionBattleReroll(Action):
    def apply(self, state):
        pass


class ActionBattleEndTurn(Action):
    def apply(self, state):
        # TODO
        for monsterID in list(state.monsters.keys()):
            monster = state.monsters.get(monsterID)
            if monster is None:
                continue
            sideID = state.monster_sides[monsterID]
            side_state = monster.sides[sideID]
            side_cls = library.Side.get_cls(side_state.name)
            targetID = state.monster_attacks[monsterID][0]
            side_cls.apply(state, side_state, targetID)

            # apply keyword logic
            for k_state in side_state.keywords.values():
                k_cls = library.Keyword.get_cls(k_state.name)
                k_cls.apply(state, side_state, monsterID, targetID)

            # TODO: inefficient
            for heroID in list(state.heroes.keys()):
                Action.check_and_remove_target(state, heroID)
            for monsterID in list(state.monsters.keys()):
                Action.check_and_remove_target(state, monsterID)
            # Action.check_and_remove_target(state, targetID)
            # Action.check_and_remove_target(state, monsterID)

        state.saved_sides.clear()
        state.table_sides.clear()
        state.monster_sides.clear()
        state.monster_attacks.clear()

        return library.Result(True)


class ActionBattleUndo(Action):
    def apply(self, state):
        pass


class ActionLevelUp(Action):
    def apply(self, state):
        state.heroes_to_select.clear()
        return library.Result(True)


class Simulator:
    def __init__(self):
        self.state = SimulatorState()
        self.heroesLib = library.HeroLib()
        self.monstersLib = library.MonsterLib()
        self.actions = []
        self.settings = {}
        self.move_to = {
            Phase.BATTLE: self._move_to_battle,
            Phase.ITEM_DISTRIBUTION: self._move_to_item_distribution,
            Phase.ITEM_SELECTION: self._move_to_item_selection,
            Phase.LEVEL_UP: self._move_to_level_up,
            Phase.FINISHED: self._move_to_finished,
        }
        self.last_fight_monsters = []

    def set_up(self, settings):
        self.settings = settings
        self.state.phase = Phase.NONE
        self.state.round = 0
        self.state.heroes_name = [self.heroesLib.getHeroBy(level=1).name for _ in range(5)]

        # self.state.items = []
        self._move_to_battle()

    def apply_actions(self, actions: List[Action]) -> List[library.Result]:
        state = self.state
        results = []
        for action in actions:
            if not self._is_action_applicable(action):
                results.apand(library.Result(False, 'Is not applicable'))
                continue
            # TODO
            if isinstance(action, ActionBattleReroll):
                self._roll()
                results.append(library.Result(True))
                continue

            actionResult = action.apply(self.state)

            # TODO
            if isinstance(action, ActionBattleEndTurn):
                if len(state.monsters) != 0 and len(state.heroes) != 0:
                    self._roll()
                    self._generate_monster_attacks()

            results.append(actionResult)

        next_phase = self._should_change_phase_to()
        if next_phase:
            self.move_to[next_phase]()

        return results

    def _roll(self):
        state = self.state
        state.table_sides.clear()
        for heroID, hero in state.heroes.items():
            sideIndex = random.randint(0, 5)
            # TODO
            side = hero.sides[sideIndex]
            state.table_sides[heroID] = side.id
        for monsterID, monster in state.monsters.items():
            sideIndex = random.randint(0, 5)
            # TODO
            side = monster.sides[sideIndex]
            state.monster_sides[monsterID] = side.id

    def _is_action_applicable(self, action):
        # TODO
        return True

    def _should_change_phase_to(self) -> Optional[Phase]:
        state = self.state
        next_phase = None
        if state.phase == Phase.BATTLE and len(state.monsters) == 0:
            # TODO
            if state.round == 20:
                next_phase = Phase.FINISHED
            else:
                next_phase = Phase.LEVEL_UP
            # if state.round == 20:
            #     next_phase = Phase.FINISHED
            # elif state.round % 2 == 0:
            #     next_phase = Phase.LEVEL_UP
            # else:
            #     next_phase = Phase.ITEM_SELECTION
        # elif state.phase == Phase.ITEM_SELECTION and not state.items_to_select:
        #     next_phase = Phase.ITEM_DISTRIBUTION
        # elif state.phase == Phase.ITEM_DISTRIBUTION and not state.is_item_distribution:
        #     next_phase = Phase.BATTLE
        elif state.phase == Phase.BATTLE and len(state.heroes) == 0:
            next_phase = Phase.FINISHED
        elif state.phase == Phase.LEVEL_UP and not state.heroes_to_select:
            next_phase = Phase.BATTLE
        return next_phase

    def _move_to_battle(self):
        state = self.state
        state.phase = Phase.BATTLE
        state.round += 1
        state.saved_sides.clear()
        state.heroes.clear()
        state.monsters.clear()
        state.monsters_position.clear()
        # python3.7 and higher has state.heroes always in the same order
        state.heroes = {
            str(uuid.uuid4()): self.heroesLib.getByName(name).dump_state()
            for name in state.heroes_name
        }
        self.state.heroes_position = OrderedDict(tuple(
            (heroID, PositionState(position=i, row=Row.FORWARD, dead=False))
            for i, heroID in enumerate(list(state.heroes.keys()))
        ))

        for hero_position in state.heroes_position.values():
            hero_position.dead = False
            hero_position.row = Row.FORWARD
        self._generate_monsters(3)

        monsters_names = []
        for monsterID in self.state.monsters:
            monster_name = self.state.monsters[monsterID].name
            monsters_names.append(monster_name)
        self.last_fight_monsters = monsters_names
        
        self._roll()
        self._generate_monster_attacks()

    def _move_to_level_up(self):
        state = self.state
        state.phase = Phase.LEVEL_UP
        state.heroes_to_select.clear()
        heroes_to_change = (
            random.sample(list(state.heroes.values()), 2)
            if len(state.heroes) > 1
            else state.heroes.values()
        )
        for hero_to_change in heroes_to_change:
            hero = self.heroesLib.getHeroBy(level=hero_to_change.level + 1, role=hero_to_change.role)
            state.heroes_to_select.append(hero.name)

    def _move_to_item_selection(self):
        pass

    def _move_to_item_distribution(self):
        pass

    def _move_to_finished(self):
        self.state.phase = Phase.FINISHED

    def _generate_monsters(self, count):
        # TODO
        allowed_monsters = self.settings.get(
            'allowed_monsters',
            list(library.MonsterLib.ALL_MONSTERS.keys()),
        )
        for i in range(count):
            monsterIndex = random.randint(0, len(allowed_monsters) - 1)
            monsterID = str(uuid.uuid4())
            monster = self.monstersLib.getByName(allowed_monsters[monsterIndex]).dump_state()
            self.state.monsters[monsterID] = monster
            self.state.monsters_position[monsterID] = PositionState(position=i, row=Row.FORWARD, dead=False)

    def _generate_monster_attacks(self):
        # TODO
        state = self.state
        for monsterID in state.monster_sides:
            heroID = random.choice(list(state.heroes.keys()))
            state.monster_attacks[monsterID] = [heroID]

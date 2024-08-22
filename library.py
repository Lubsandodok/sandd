import abc
import random
from typing import List, Self, Optional, Dict, OrderedDict, Literal

import state


class Result:
    def __init__(self, success, msg=''):
        self.success = success
        self.msg = msg


class Keyword(abc.ABC):
    ALL_KEYWORDS = {}

    @classmethod
    def get_cls(cls, name):
        return cls.ALL_KEYWORDS[name]

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @classmethod
    @abc.abstractmethod
    def apply(cls, state, side_state, selfID, targetID) -> Result:
        pass

    @classmethod
    @abc.abstractmethod
    def undo(cls, state, side_state, selfID, targetID) -> Result:
        pass

    @abc.abstractmethod
    def dump_state(self) -> state.KeywordState:
        pass


class Death(Keyword):
    @classmethod
    def name(cls) -> str:
        return 'death'

    @classmethod
    def apply(cls, state, side_state, selfID, targetID) -> Result:
        if selfID in state.monsters:
            character_state = state.monsters[selfID]
        elif selfID in state.heroes:
            character_state = state.heroes[selfID]
        Character.die(character_state)
        return Result(True)

    @classmethod
    def undo(cls, state, target_state, selfID, targetID) -> Result:
        pass

    # def on_end_turn(cls, state, target_state, selfID, targetID) -> Result:
    #     pass

    def dump_state(self) -> state.KeywordState:
        return state.KeywordState(name=self.name())


class Petrify(Keyword):
    @classmethod
    def name(self) -> str:
        return 'petrify'

    @classmethod
    def apply(cls, state, side_state, selfID, targetID) -> Result:
        character_state = None
        if targetID in state.monsters:
            character_state = state.monsters[targetID]
        elif targetID in state.heroes:
            character_state = state.heroes[targetID]
        if character_state:
            Character.petrify(character_state)
        return Result(True)

    @classmethod
    def undo(cls, state, target_state, selfID, targetID) -> Result:
        pass

    def dump_state(self) -> state.KeywordState:
        return state.KeywordState(name=self.name())


class Eliminate(Keyword):
    @classmethod
    def name(self) -> str:
        return 'eliminate'

    @classmethod
    def apply(cls, state, side_state, selfID, targetID) -> Result:
        pass

    def dump_state(self) -> state.KeywordState:
        return state.KeywordState(name=self.name())


class Cleave(Keyword):
    @classmethod
    def name(self) -> str:
        return 'cleave'

    @classmethod
    def apply(cls, state_obj: state.SimulatorState, side_state, selfID, targetID) -> Result:
        # TODO: refactor it later. Balanced trees would be ideal here.
        def get_value(
                positions: OrderedDict[CharacterID, state.PositionState],
                targetID: CharacterID,
                direction: Literal[-1, 1],
        ) -> Optional[CharacterID]:
            position_list = list(positions.keys())
            position = positions[targetID].position + direction
            can_iterate = position not in (-1, len(positions))
            while can_iterate:
                characterID = position_list[position]
                if positions[characterID].dead == False:
                    return characterID
                position += direction
                can_iterate = position not in (-1, len(positions))
            return None

        if targetID in state_obj.monsters:
            # The third one exists in the side itself
            monsters_to_attack = [
                get_value(state_obj.monsters_position, targetID, 1),
                get_value(state_obj.monsters_position, targetID, -1),
            ]
            for monsterID in monsters_to_attack:
                if monsterID:
                    side_cls = Side.get_cls(side_state.name)
                    side_cls.apply(state_obj, side_state, monsterID)
        elif targetID in state_obj.heroes:
            heroes_to_attack = [
                get_value(state_obj.heroes_position, targetID, 1),
                get_value(state_obj.heroes_position, targetID, -1),
            ]
            for heroID in heroes_to_attack:
                if heroID:
                    side_cls = Side.get_cls(side_state.name)
                    side_cls.apply(state_obj, side_state, heroID)
        return Result(True)

    @classmethod
    def undo(cls, state, target_state, selfID, targetID) -> Result:
        pass

    def dump_state(self) -> state.KeywordState:
        return state.KeywordState(name=self.name())


class Side(abc.ABC):
    ALL_SIDES = {}

    def __init__(self, id, pip, keywords=None):
        self.id = id
        self.pip = pip
        self.keywords = {k.name(): k() for k in keywords} if keywords else dict()

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @classmethod
    @abc.abstractmethod
    def apply(cls, state, side_state, targetID) -> Result:
        pass

    @classmethod
    def get_cls(cls, name):
        return cls.ALL_SIDES[name]

    # TODO
    def dump_state(self):
        return state.SideState(
            id=self.id,
            pip=self.pip,
            name=self.name(),
            keywords={name: k.dump_state() for name, k in self.keywords.items()},
        )


class SideSword(Side):
    @classmethod
    def name(self):
        return 'sword'

    @classmethod
    def apply(self, state, side_state, targetID) -> Result:
        target_state = None
        if targetID in state.monsters:
            target_state = state.monsters[targetID]
        elif targetID in state.heroes:
            target_state = state.heroes[targetID]
        if target_state:
            Character.takeDamage(target_state, side_state.pip)
        return Result(True)


class SideShield(Side):
    @classmethod
    def name(self):
        return 'shield'

    @classmethod
    def apply(self, state, side_state, targetID) -> Result:
        target_state = None
        if targetID in state.monsters:
            target_state = state.monsters[targetID]
        elif targetID in state.heroes:
            target_state = state.heroes[targetID]
        if target_state:
            Character.addShield(target_state, side_state.pip)
        return Result(True)


CharacterState = state.HeroState | state.MonsterState
CharacterID = state.HeroID | state.MonsterID


class Character:
    name: str
    health: int
    sides: List[Side]  # TODO: type
    shield: Optional[int]

    def __init__(self, name, health, sides, shield=0):
        self.name = name
        self.health = health
        self.sides = sides
        self.shield = shield

    @classmethod
    # TODO: const
    def can_side_be_used(cls, character_state: CharacterState, sideID: state.SideID) -> bool:
        for effect in character_state.effects.values():
            if effect.name == state.EffectName.PETRIFY:
                if sideID in character_state.effects[state.EffectName.PETRIFY].sides:
                    return False
        return True

    @classmethod
    def takeDamage(cls, character_state: CharacterState, damage):
        cs = character_state
        if cs.shield != 0 and cs.shield >= damage:
            cs.shield -= damage
        elif cs.shield != 0 and cs.shield < damage:
            cs.shield = 0
            cs.health -= (damage - cs.shield)
        else:
            cs.health -= damage

    @classmethod
    def die(cls, character_state: CharacterState):
        cs = character_state
        cs.shield = 0
        cs.health = 0

    @classmethod
    def addShield(cls, character_state: CharacterState, shield: int):
        character_state.shield += shield

    @classmethod
    def petrify(cls, character_state: CharacterState):
        # print(character_state)
        def next_side_to_petrify(current: List[state.SideID]) -> state.SideID:
            # TODO: generator and -1
            return {
                -1: 4,
                4: 0,
                0: 1,
                1: 2,
                2: 3,
                3: 5,
                5: -1,
            }[current[-1] if current else -1]

        cs = character_state
        name = state.EffectName.PETRIFY
        if name not in cs.effects:
            cs.effects[name] = state.PetrifyEffectState(name=name, sides=list())

        for _ in range(2):
            next_side = next_side_to_petrify(cs.effects[name].sides)
            if next_side != -1:
                cs.effects[name].sides.append(next_side)


class Hero(Character):
    level: int
    role: state.HeroRole

    def __init__(self, name, health, level, role, sides, shield=0):
        super().__init__(name, health, sides, shield)
        self.level = level
        self.role = role

    @classmethod
    def create(cls, name: str) -> Self:
        if name not in HeroLib.ALL_HEROES:
            return
        health, level, role, sideDescrs = HeroLib.ALL_HEROES[name]
        sides = []
        for index, sideDescr in enumerate(sideDescrs):
            sideCls, args = sideDescr
            sides.append(sideCls(index, *args))
        hero = cls(name, health, level, role, sides)
        return hero

    def dump_state(self) -> state.HeroState:
        return state.HeroState(
            name=self.name,
            health=self.health,
            level=self.level,
            role=self.role,
            shield=self.shield,
            sides=[side.dump_state() for side in self.sides],
            effects=dict(),
        )


class HeroLib:
    ALL_HEROES: Dict[str, tuple] = {}  # TODO: type
    heroes: Dict[str, Hero]

    def __init__(self):
        self.settings = {}
        self.heroes = {
            name: Hero.create(name)
            for name in self.ALL_HEROES
        }

    def set_up(self, settings: dict):
        self.settings = settings
        # TODO
        self.allowed_heroes = self.settings.get('allowed_heroes', set(self.ALL_HEROES.keys()))

    def getByName(self, name: str) -> Hero:
        return self.heroes[name]

    def getHeroBy(self, level: Optional[int] = None, role: Optional[state.HeroRole] = None) -> Hero:
        def filterFunc(hero):
            if level and hero.level != level:
                return False
            if role and hero.role != role:
                return False
            return True

        return random.choice(list(filter(filterFunc, self.heroes.values())))


class Monster(Character):
    def __init__(self, name, health, sides, shield=0):
        super().__init__(name, health, sides, shield)

    @classmethod
    def create(cls, name: str) -> Self:
        if name not in MonsterLib.ALL_MONSTERS:
            return
        health, sideDescrs = MonsterLib.ALL_MONSTERS[name]
        sides = []
        for index, sideDescr in enumerate(sideDescrs):
            sideCls, args = sideDescr
            sides.append(sideCls(index, *args))
        monster = cls(name, health, sides)
        return monster

    def dump_state(self) -> state.MonsterState:
        return state.MonsterState(
            name=self.name,
            health=self.health,
            shield=self.shield,
            sides=[side.dump_state() for side in self.sides],
            effects=dict(),
        )


class MonsterLib:
    ALL_MONSTERS = {}

    def __init__(self):
        self.monsters = {
            name: Monster.create(name)
            for name in self.ALL_MONSTERS
        }

    def getByName(self, name):
        return self.monsters[name]


Keyword.ALL_KEYWORDS = {
    k_cls.name(): k_cls
    for k_cls in (Death, Petrify, Cleave)
}


Side.ALL_SIDES = {
    side_cls.name(): side_cls
    for side_cls in (SideSword, SideShield)
}


HeroLib.ALL_HEROES = {
    'fighter': (
        5,
        1,
        state.HeroRole.YELLOW,
        (
            (SideSword, (2,)),
            (SideSword, (2,)),
            (SideShield, (1,)),
            (SideShield, (1,)),
            (SideSword, (1,)),
            (SideSword, (1,)),
        ),
    ),
    'defender': (
        7,
        1,
        state.HeroRole.GREY,
        (
            (SideShield, (3,)),
            (SideShield, (2,)),
            (SideShield, (1,)),
            (SideSword, (0,)),  # TODO: this should be empty
            (SideSword, (1,)),
            (SideSword, (1,)),
        ),
    ),
    'soldier': (
        7,
        2,
        state.HeroRole.YELLOW,
        (
            (SideSword, (3,)),
            (SideSword, (3,)),
            (SideShield, (2,)),
            (SideShield, (2,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
        ),
    ),
    'warden': (
        10,
        2,
        state.HeroRole.GREY,
        (
            (SideShield, (4,)),
            (SideShield, (3,)),
            (SideShield, (2,)),
            (SideShield, (1,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
        ),
    ),
}


MonsterLib.ALL_MONSTERS = {
    'rat': (
        3,
        (
            (SideSword, (3,)),
            (SideSword, (3,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
        ),
    ),
    'bee': (
        2,
        (
            (SideSword, (4, (Death,))),
            (SideSword, (4, (Death,))),
            (SideSword, (1,)),
            (SideSword, (1,)),
            (SideSword, (1,)),
            (SideSword, (1,)),
        ),
        ),
    'wolf': (
        6,
        (
            (SideSword, (4,)),
            (SideSword, (4,)),
            (SideSword, (1,)),
            (SideSword, (1,)),
            (SideSword, (3,)),
            (SideSword, (3,)),
        ),
    ),
    'archer': (
        2,
        (
            (SideSword, (3,)),
            (SideSword, (3,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
            (SideSword, (2,)),
        ),
    ),
    # 'alpha': (
    #     13,
    #     (
    #         (SideSword, (2,)),
    #         (SideSword, (2,)),
    #         (SideSummon, (1, 'wolf')),
    #         (SideSummon, (1, 'wolf')),
    #         (SideSword, (6,)),
    #         (SideSword, (6,)),
    #     ),
    # ),
}

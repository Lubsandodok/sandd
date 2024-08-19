import dataclasses
import enum
from typing import Dict, List, Set


HeroID = str
SideID = int
MonsterID = str
ItemID = str


class Phase(enum.Enum):
    NONE = enum.auto()
    LEVEL_UP = enum.auto()
    ITEM_SELECTION = enum.auto()
    ITEM_DISTRIBUTION = enum.auto()
    BATTLE = enum.auto()
    FINISHED = enum.auto()


class HeroRole(enum.Enum):
    YELLOW = enum.auto()
    GREY = enum.auto()


class EffectName(enum.Enum):
    PETRIFY = enum.auto()


@dataclasses.dataclass
class KeywordState:
    name: str


@dataclasses.dataclass
class EffectState:
    name: str


@dataclasses.dataclass
class PetrifyEffectState(EffectState):
    sides: List[SideID]


@dataclasses.dataclass
class SideState:
    id: int
    pip: int
    name: str
    keywords: Dict[str, KeywordState]


@dataclasses.dataclass
class HeroState:
    name: str
    health: int
    level: int
    role: HeroRole
    shield: int
    sides: List[SideState]
    effects: Dict[EffectName, EffectState]


@dataclasses.dataclass
class MonsterState:
    name: str
    health: int
    shield: int
    sides: List[SideState]
    effects: Dict[EffectName, EffectState]


@dataclasses.dataclass
class SimulatorState:
    round: int = 0
    phase: Phase = Phase.NONE
    is_item_distribution: bool = False

    heroes_names: List[str] = dataclasses.field(default_factory=str)
    heroes: Dict[HeroID, HeroState] = dataclasses.field(default_factory=dict)
    monsters: Dict[MonsterID, MonsterState] = dataclasses.field(default_factory=dict)
    # items: List[Item]

    table_sides: Dict[HeroID, SideID] = dataclasses.field(default_factory=dict)
    saved_sides: Dict[HeroID, SideID] = dataclasses.field(default_factory=dict)
    monster_sides: Dict[MonsterID, SideID] = dataclasses.field(default_factory=dict)
    monster_attacks: Dict[MonsterID, List[HeroID]] = dataclasses.field(default_factory=dict)

    heroes_to_select: List[str] = dataclasses.field(default_factory=list)
    items_to_select: List[ItemID] = dataclasses.field(default_factory=list)

    def serialize(self):
        pass

    def deserialize(self):
        pass

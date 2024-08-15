import abc
import random

from state import HeroRole, HeroState, MonsterState, SideState


class Result:
    def __init__(self, success, msg=''):
        self.success = success
        self.msg = msg


class Side(abc.ABC):
    ALL_SIDES = {}

    def __init__(self, id, pip):
        self.id = id
        self.pip = pip

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @classmethod
    @abc.abstractmethod
    def apply(cls, state, side_state, targetID) -> Result:
        pass

    @classmethod
    def get_side_cls(cls, name):
        return cls.ALL_SIDES[name]

    # TODO
    def dumpState(self):
        return SideState(id=self.id, pip=self.pip, name=self.name())


class SideSword(Side):
    @classmethod
    def name(self):
        return 'sword'

    @classmethod
    def apply(self, state, side_state, targetID) -> Result:
        if targetID in state.monsters:
            target_state = state.monsters[targetID]
            Monster.takeDamage(target_state, side_state.pip)
        elif targetID in state.heroes:
            target_state = state.heroes[targetID]
            Hero.takeDamage(target_state, side_state.pip)
        return Result(True)


class SideShield(Side):
    @classmethod
    def name(self):
        return 'shield'

    @classmethod
    def apply(self, state, side_state, targetID) -> Result:
        if targetID in state.monsters:
            target_state = state.monsters[targetID]
            Monster.addShield(target_state, side_state.pip)
        elif targetID in state.heroes:
            target_state = state.heroes[targetID]
            Hero.addShield(target_state, side_state.pip)
        return Result(True)


class Hero:
    def __init__(self, name, health, level, role, sides, shield=0):
        self.name = name
        self.health = health
        self.level = level
        self.role = role
        self.sides = sides
        self.shield = shield

    @classmethod
    def create(cls, name):
        if name not in HeroLib.ALL_HEROES:
            return
        health, level, role, sideDescrs = HeroLib.ALL_HEROES[name]
        sides = []
        for index, sideDescr in enumerate(sideDescrs):
            sideCls, args = sideDescr
            sides.append(sideCls(index, *args))
        hero = cls(name, health, level, role, sides)
        return hero

    def dumpState(self):
        return HeroState(
            name=self.name,
            health=self.health,
            level=self.level,
            role=self.role,
            shield=self.shield,
            sides=[side.dumpState() for side in self.sides],
        )

    @classmethod
    def takeDamage(cls, hero_state, damage):
        ms = hero_state
        if ms.shield != 0 and ms.shield >= damage:
            ms.shield -= damage
        elif ms.shield != 0 and ms.shield < damage:
            ms.shield = 0
            ms.health -= (damage - ms.shield)
        else:
            ms.health -= damage

    @classmethod
    def addShield(cls, hero_state, shield):
        hero_state.shield += shield


class HeroLib:
    ALL_HEROES = {}

    def __init__(self):
        self.settings = {}
        self.heroes = {
            name: Hero.create(name)
            for name in self.ALL_HEROES
        }

    def set_up(self, settings):
        self.settings = settings
        # TODO
        self.allowed_heroes = self.settings.get('allowed_heroes', set(self.ALL_HEROES.keys()))

    def getByName(self, name):
        return self.heroes[name]

    def getHeroBy(self, level=None, role=None):
        def filterFunc(hero):
            if level and hero.level != level:
                return False
            if role and hero.role != role:
                return False
            return True

        return random.choice(list(filter(filterFunc, self.heroes.values())))


class Monster:
    def __init__(self, name, health, sides, shield=0):
        self.name = name
        self.health = health
        self.sides = sides
        self.shield = shield

    @classmethod
    def create(cls, name):
        if name not in MonsterLib.ALL_MONSTERS:
            return
        health, sideDescrs = MonsterLib.ALL_MONSTERS[name]
        sides = []
        for index, sideDescr in enumerate(sideDescrs):
            sideCls, args = sideDescr
            sides.append(sideCls(index, *args))
        monster = cls(name, health, sides)
        return monster

    def dumpState(self):
        return MonsterState(
            name=self.name,
            health=self.health,
            shield=self.shield,
            sides=[side.dumpState() for side in self.sides],
        )

    @classmethod
    def takeDamage(cls, monster_state, damage):
        ms = monster_state
        if ms.shield != 0 and ms.shield >= damage:
            ms.shield -= damage
        elif ms.shield != 0 and ms.shield < damage:
            ms.shield = 0
            ms.health -= (damage - ms.shield)
        else:
            ms.health -= damage

    @classmethod
    def addShield(cls, monster_state, shield):
        monster_state.shield += shield


class MonsterLib:
    ALL_MONSTERS = {}

    def __init__(self):
        self.monsters = {
            name: Monster.create(name)
            for name in self.ALL_MONSTERS
        }

    def getByName(self, name):
        return self.monsters[name]


Side.ALL_SIDES = {
    sideCls.name(): sideCls
    for sideCls in (SideSword, SideShield)
}


HeroLib.ALL_HEROES = {
    'fighter': (
        5,
        1,
        HeroRole.YELLOW,
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
        HeroRole.GREY,
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
        HeroRole.YELLOW,
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
        HeroRole.GREY,
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
            (SideSword, (4,)),
            (SideSword, (4,)),
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

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
        self.last_fight_monsters = []

    def run(self):
        s = self.simulator
        s.set_up({'allowed_monsters': ['bee']})
        while s.state.phase != state.Phase.FINISHED:
            while s.state.phase not in (state.Phase.LEVEL_UP, state.Phase.FINISHED):
                self._step_battle()
            self._step_level_up()
        return s.state.round, self.last_fight_monsters

    def _step_battle(self):
        s = self.simulator
        self.last_fight_monsters = s.last_fight_monsters

        for heroID in s.state.heroes:
            s.apply_actions([ActionBattleSaveSide([heroID])])
        for heroID in s.state.heroes:
            if len(s.state.monsters) != 0:
                sideID = s.state.saved_sides[heroID]

                attacked_heroID_list = []
                for attacked_heroID in s.state.monster_attacks.values():
                    attacked_heroID_list += attacked_heroID

                heroes_hp_dict = {}
                for heroId in s.state.heroes:
                    health = s.state.heroes[heroId].health
                    heroes_hp_dict[heroId] = health

                heroes_shield_dict = {}
                for heroId in s.state.heroes:
                    shield = s.state.heroes[heroId].shield
                    heroes_shield_dict[heroId] = shield

                monster_hp_dict = {}
                min_monster_hp = 999
                for MonsterID in s.state.monsters:
                    health = s.state.monsters[MonsterID].health
                    if health < min_monster_hp:
                        min_monster_hp = health
                    monster_hp_dict[MonsterID] = health

                monster_target_dict = {}
                for monsterID in s.state.monster_attacks:
                    target_list = s.state.monster_attacks[monsterID]
                    for heroId in target_list:
                        monster_target_dict[monsterID] = heroId

                monster_pip_dict = {}
                max_attack_with_min_hp = 0
                max_attack_with_min_hp_ID = 0
                for monsterID in s.state.monster_sides:
                    sideID = s.state.monster_sides[monsterID]
                    pip = s.monstersLib.getByName(s.state.monsters[monsterID].name).sides[sideID].pip
                    if monster_hp_dict[monsterID] == min_monster_hp:
                        if pip > max_attack_with_min_hp:
                            max_attack_with_min_hp = pip
                            max_attack_with_min_hp_ID = monsterID
                    monster_pip_dict[monsterID] = pip
                
                heroes_damaged_by_dict = {}
                for monsterID in monster_pip_dict:
                    heroId = monster_target_dict[monsterID]
                    pip = monster_pip_dict[monsterID]
                    if heroId not in heroes_damaged_by_dict:
                        heroes_damaged_by_dict[heroId] = {}  
                    heroes_damaged_by_dict[heroId][monsterID] = pip

                heroes_damadge_list = {}
                for heroId in heroes_damaged_by_dict:
                    damage = 0
                    for monsterID in heroes_damaged_by_dict[heroId]:
                        damage += pip
                    health = heroes_hp_dict[heroId]
                    shield = heroes_shield_dict[heroId]
                    heroes_damadge_list[heroId] = health + shield - damage
                heroes_damadge_list = dict(sorted(heroes_damadge_list.items(), key=lambda item: item[1]))

                heroes_dying_list = {}
                for heroId in heroes_damaged_by_dict:
                    damage = 0
                    for monsterID in heroes_damaged_by_dict[heroId]:
                        damage += pip
                    health = heroes_hp_dict[heroId]
                    shield = heroes_shield_dict[heroId]
                    if damage >= health + shield:
                        heroes_dying_list[heroId] = health + shield - damage
                
                heroes_dying_list = dict(sorted(heroes_dying_list.items(), key=lambda item: item[1]))

                killing_monsters = []
                for heroId in heroes_dying_list:
                    for monsterID in heroes_damaged_by_dict[heroId]:
                        killing_monsters.append(monsterID)
                
                killing_monster_min_hp = 999
                for monsterID in killing_monsters:
                    hp = monster_hp_dict[monsterID]
                    if hp < killing_monster_min_hp:
                        killing_monster_min_hp = hp


                least_killing_hp_monsters = {}
                for monsterID in killing_monsters:
                    if monster_hp_dict[monsterID] == killing_monster_min_hp:
                        damage = monster_pip_dict[monsterID]
                        least_killing_hp_monsters[monsterID] = damage

                least_killing_hp_monsters = dict(sorted(least_killing_hp_monsters.items(), key=lambda item: item[1], reverse=True))
                # least_killing_hp_monsters = dict(sorted(least_killing_hp_monsters.items(), key=lambda item: item[1]))

                if isinstance(
                    s.heroesLib.getByName(s.state.heroes[heroID].name).sides[sideID],
                    library.SideSword,
                ):
                    # targetID = random.choice(list(s.state.monsters.keys()))
                    # if least_killing_hp_monsters:
                    #     targetID = next(iter(least_killing_hp_monsters))
                    # else:
                    #     targetID = max_attack_with_min_hp_ID

                    targetID = max_attack_with_min_hp_ID
                else:
                    # targetID = random.choice(list(s.state.heroes.keys()))
                    if heroes_dying_list:
                        targetID = next(iter(heroes_dying_list))
                    else:
                        targetID = next(iter(heroes_damadge_list))
                s.apply_actions([ActionBattleApplySide(heroID, sideID, targetID)])
        s.apply_actions([ActionBattleEndTurn()])

    def _step_level_up(self):
        s = self.simulator
        s.apply_actions([ActionLevelUp()])
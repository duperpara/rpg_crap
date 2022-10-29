import json
from copy import copy
from time import sleep
from typing import List
import re
from d20 import roll as roll_dice

ROLL_LOCAL = True


def rollroll(roll: str) -> int:
    if ROLL_LOCAL:
        r = roll_dice(roll)
        print(f"Roll result: {r.result}\n")
        return r.total
    else:
        while True:
            try:
                return int(input("Input Roll Result: "))
            except ValueError:
                print("Invalid input")


class ActionTypes:
    action = 'action'
    bonus_action = 'bonus_action'
    reaction = 'reaction'
    single_use = 'single_use'
    unlimited = 'unlimited'
    passive = 'passive'


class ActionCategories:
    attack = 'attack'
    action = 'action'
    buff = 'buff'
    defense = 'defense'


class TurnStats:
    def __init__(self, base_action_qt: int = 1, base_bonus_action_qt: int = 1,
                 base_extra_attack_qt: int = 0, base_reaction_qt: int = 1):
        self._base_action_qt = base_action_qt
        self._base_bonus_action_qt = base_bonus_action_qt
        self._base_extra_attack_qt = base_extra_attack_qt
        self._base_reaction_qt = base_reaction_qt

        self.start_turn_action_qt = base_action_qt
        self.start_turn_bonus_action_qt = base_bonus_action_qt
        self.start_turn_extra_attack_qt = base_extra_attack_qt
        self.start_turn_reaction_qt = base_reaction_qt

        self.current_turn_action_qt = 0
        self.current_turn_bonus_action_qt = 0
        self.current_turn_extra_attack_qt = 0
        self.current_turn_reaction_qt = 0

        self.current_roll = ''
        self.current_attack_base_stat = None
        self.current_dmg_type = None
        self.current_distance = None

        self.due_damage = 0

    def _end_turn(self):
        self.current_turn_action_qt = 0
        self.current_turn_bonus_action_qt = 0
        self.current_turn_extra_attack_qt = 0

    def _start_turn(self):
        self.current_turn_action_qt = self.start_turn_action_qt
        self.current_turn_bonus_action_qt = self.start_turn_bonus_action_qt
        self.current_turn_extra_attack_qt = self.start_turn_extra_attack_qt
        self.current_turn_reaction_qt = self.start_turn_reaction_qt

    def __repr__(self):
        return f'A: {self.current_turn_action_qt}  B: {self.current_turn_bonus_action_qt}  ' \
               f'EX: {self.current_turn_extra_attack_qt}  R: {self.current_turn_reaction_qt}'


class Stats:
    def __init__(self, *, MAX_HP: int, current_hp: int = None, FOR: int, RES: int, INT: int,
                 SOR: int, CAR: int, VEL: int, move_speed: float, weapon_mastery: str, def_die: str):
        self.MAX_HP = MAX_HP

        self.current_hp = current_hp
        if current_hp is None:
            self.current_hp = MAX_HP

        self.FOR = FOR
        self.RES = RES
        self.INT = INT
        self.SOR = SOR
        self.CAR = CAR
        self.VEL = VEL
        self.move_speed = move_speed
        self.weapon_mastery = weapon_mastery
        self.def_die = def_die

    def __repr__(self):
        return ' '.join([f'{key}: {value}' for key, value in self.get_dict().items()])

    def get_dict(self):
        return {
            "MAX_HP": self.MAX_HP,
            "current_hp": self.current_hp,
            "FOR": self.FOR,
            "RES": self.RES,
            "INT": self.INT,
            "SOR": self.SOR,
            "CAR": self.CAR,
            "VEL": self.VEL,
            "move_speed": self.move_speed,
            "weapon_mastery": self.weapon_mastery,
            "def_die": self.def_die,
        }

    def add_stats(self, delta_stats: dict):
        for key, item in delta_stats.items():
            if isinstance(item, str):
                if item != "":
                    setattr(self, key, getattr(self, key) + " + " + item)
            else:
                setattr(self, key, getattr(self, key) + item)


class HookCallbacks:
    on_attack = 'on_attack'
    on_defense = 'on_defense'
    on_hook = 'on_hook'
    on_end = 'on_end'
    on_damage = 'on_damage'


class HookActions:
    class AtkBonus:
        key = 'atk_bonus'
        callbacks = [HookCallbacks.on_attack]

        @staticmethod
        def action(hook_data: dict, dto):
            condition = hook_data.get('condition')
            if (
                    condition is None
                    or (condition == 'FOR_atk' and 'FOR' == dto['turn_stats'].current_attack_base_stat)
                    or (condition == 'electric_attack' and dto['turn_stats'].current_dmg_type == 'electric')
                    or (condition == 'melee_atk' and dto['turn_stats'].current_distance == 'melee')
            ):
                dto['turn_stats'].current_roll += " + " + hook_data.get('roll')

    class DefBonus:
        key = 'def_bonus'
        callbacks = [HookCallbacks.on_defense]

        @staticmethod
        def action(hook_data: dict, dto):
            bonus = hook_data.get('roll')
            if r'//' in bonus:
                split_bonus = re.split(r'\s', bonus)
                for stat_name, stat_value in dto.get('stats').get_dict().items():
                    split_bonus = [bon.replace(stat_name, str(stat_value)) for bon in split_bonus]
                new_bonus = []
                for bon in split_bonus:
                    if r'//' in bon:
                        bon = bon.split(r'//')
                        bon = str(int(bon[0])//int(bon[1]))
                    new_bonus.append(bon)
                new_bonus = ' '.join(new_bonus)
                bonus = new_bonus

            dto['turn_stats'].current_roll += " + " + bonus

    class ExtraAtk:
        key = 'extra_atk'
        callbacks = [HookCallbacks.on_hook, HookCallbacks.on_end]

        @staticmethod
        def action(hook_data: dict, dto):
            if hook_data.get('keep'):
                if hook_data.get('used_flag'):
                    dto['turn_stats'].start_turn_extra_attack_qt -= hook_data.get('qt')
                else:
                    hook_data['used_flag'] = True
                    dto['turn_stats'].start_turn_extra_attack_qt += hook_data.get('qt')

            dto['turn_stats'].current_turn_extra_attack_qt += hook_data.get('qt')

    class ExtraAction:
        key = 'extra_action'
        callbacks = [HookCallbacks.on_hook, HookCallbacks.on_end]

        @staticmethod
        def action(hook_data: dict, dto):
            if hook_data.get('keep'):
                if hook_data.get('used_flag'):
                    dto['turn_stats'].start_turn_action_qt -= hook_data.get('qt')
                else:
                    hook_data['used_flag'] = True
                    dto['turn_stats'].start_turn_action_qt += hook_data.get('qt')

            dto['turn_stats'].current_turn_action_qt += hook_data.get('qt')

    class ExtraBonusAction:
        key = 'extra_bonus_action'
        callbacks = [HookCallbacks.on_hook, HookCallbacks.on_end]

        @staticmethod
        def action(hook_data: dict, dto):
            if hook_data.get('keep'):
                if hook_data.get('used_flag'):
                    dto['turn_stats'].start_turn_bonus_action_qt -= hook_data.get('qt')
                else:
                    hook_data['used_flag'] = True
                    dto['turn_stats'].start_turn_bonus_action_qt += hook_data.get('qt')

            dto['turn_stats'].current_turn_bonus_action_qt += hook_data.get('qt')

    class StatPlus:
        key = 'stat_plus'
        callbacks = [HookCallbacks.on_hook, HookCallbacks.on_end]

        @staticmethod
        def action(hook_data: dict, dto):
            for stat_name in hook_data.keys():
                if isinstance(hook_data.get(stat_name), str):
                    for key, value in dto.stats.get_dict().items():
                        hook_data[stat_name] = hook_data.get(stat_name).replace(key, str(value))
                    hook_data[stat_name] = int(hook_data[stat_name])
                    plus = hook_data.get(stat_name)
                else:
                    plus = hook_data.get(stat_name)

                dto.stats.add_stats({stat_name: plus})
                hook_data[stat_name] = -hook_data[stat_name]

    class Heal:
        key = 'heal'
        callbacks = [HookCallbacks.on_hook]

        @staticmethod
        def action(hook_data: dict, dto):
            rl = rollroll(hook_data.get('roll'))
            dto['stats'].current_hp += rl
            if dto['stats'].current_hp > dto['stats'].MAX_HP:
                print("Overhealed!")
                dto['stats'].current_hp = dto['stats'].MAX_HP

    class Shield:
        key = 'shield'
        callbacks = [HookCallbacks.on_damage]

        @staticmethod
        def action(hook_data: dict, dto):
            shield = hook_data.get('shield')
            res = shield - dto.get('turn_stats').due_damage
            hook_data['shield'] = res
            if res < 0:
                dto['turn_stats'].due_damage -= shield
                hook_data['shield'] = 0
            else:
                dto['turn_stats'].due_damage = 0
                hook_data['shield'] = res

    class Revive:
        key = 'revive'
        callbacks = [HookCallbacks.on_damage]

        @staticmethod
        def action(hook_data: dict, dto):
            if dto.get('turn_stats').due_damage >= dto.get('stats').current_hp:
                dto['turn_stats'].due_damage = 0
                dto['stats'].current_hp = hook_data.get('hp', 1)

    class DefAdv:
        key = 'def_adv'
        callbacks = [HookCallbacks.on_defense]

        @staticmethod
        def action(hook_data: dict, dto):
            dv = '2d20kh1' if ROLL_LOCAL else '1dv20'
            dto['turn_stats'].current_roll = dto['turn_stats'].current_roll.replace(
                'def_die', dto.get('stats').def_die.replace('1d20', dv))

    class RechargeSpell:
        key = 'recharge_spell'
        callbacks = [HookCallbacks.on_hook]

        @staticmethod
        def action(hook_data: dict, dto):
            while True:
                try:
                    parent_idx = int(input("Input Roll Result: "))
                    break
                except ValueError:
                    print("Invalid input")
            dto['spells'][parent_idx].cur_uses += hook_data.get('qt')

    class IncBonus:
        key = 'inc_bonus'
        callbacks = [HookCallbacks.on_hook, HookCallbacks.on_end]

        @staticmethod
        def action(hook_data: dict, dto):
            pass

    hook_actions = {
        AtkBonus.key: AtkBonus,
        DefBonus.key: DefBonus,
        ExtraAtk.key: ExtraAtk,
        ExtraAction.key: ExtraAction,
        ExtraBonusAction.key: ExtraBonusAction,
        StatPlus.key: StatPlus,
        Heal.key: Heal,
        Shield.key: Shield,
        Revive.key: Revive,
        DefAdv.key: DefAdv,
        RechargeSpell.key: RechargeSpell,
        IncBonus.key: IncBonus,
    }


class Hook:
    def __init__(self, *, key: str, data: dict, parent: str, duration: int):
        hook_action = HookActions.hook_actions.get(key)
        self.key = key
        self.callbacks = hook_action.callbacks
        self.action = hook_action.action
        self.data = copy(data)
        self.parent = parent
        self.duration = duration

    def __repr__(self):
        msg = f'{self.parent}: {self.key} [{self.duration}] turns left'
        if self.data:
            msg += f' - {" ".join([f"{key}: {value}" for key, value in self.data.items()])}'
        return msg

    def call(self, dto):
        self.action(self.data, dto)


class Action:
    def __init__(self, *, name: str, category: str, dmg_type: str = None, distance: str = None, base_stat: str = None,
                 roll: str):
        self.name = name
        self.category = category
        self.dmg_type = dmg_type
        self.distance = distance
        self.base_stat = base_stat
        self.roll = roll

    def __repr__(self):
        return self.name


class CharInfo:
    def __init__(self, *, name, level, exp, karma):
        self.name = name
        self.level = level
        self.exp = exp
        self.karma = karma

    def __repr__(self):
        return self.name


class Equipment:
    def __init__(self, *, name: str, category, defense: str = None, stat_plus: dict = None,
                 description: str, hooks: dict = None):
        self.name = name
        self.category = category
        self.defense = defense
        self.stat_plus = stat_plus
        self.description = description
        self.hooks = None
        if hooks is not None:
            self.hooks = [Hook(
                key=key, data=data, parent=name, duration=999
            ) for hook in hooks for key, data in hook.items()]

    def __repr__(self):
        return self.name


class Spell:
    def __init__(self, *, name: str, level: int, description: str, action_type: str, category: str,
                 uses: int, duration: int = 0, concentration_flag: bool = None, dmg_type: str = None,
                 roll: str = None, test: str = None, hooks: list = None, test_description: str = None):
        self.name = name
        self.level = level
        self.description = description
        self.action_type = action_type
        self.category = category
        self.uses = uses
        self.cur_uses = uses
        self.duration = duration
        self.concentration_flag = concentration_flag
        self.dmg_type = dmg_type
        self.roll = roll
        self.test = test
        self.test_description = test_description
        self.hooks = None
        if hooks is not None:
            self.hooks = [Hook(
                key=key, data=data, parent=name, duration=duration
            ) for hook in hooks for key, data in hook.items()]

    def dict(self) -> dict:
        return {'name': self.name,
                'level': self.level,
                'action_type': self.action_type,
                'category': self.category,
                'uses': self.uses,
                'duration': self.duration,
                'concentration_flag': self.concentration_flag,
                'dmg_type': self.dmg_type,
                'roll': self.roll,
                'test': self.test,
                'hooks': self.hooks,
                'description': self.description}

    def regain_uses(self, qt: int = None):
        if qt is None:
            qt = self.uses
        if self.cur_uses + qt <= self.uses:
            self.cur_uses += qt
        else:
            print('Cannot regain uses above maximum')

    def __repr__(self):
        return self.name


class Trait(Spell):
    pass


class Character:
    def __init__(self, char_json: str):
        with open(char_json, 'rb') as json_obj:
            data = json.load(json_obj).get('character')

        self.info = self.parse_info(data.get('info'))
        self.base_stats = self.parse_stats(data.get('stats'))
        self.equipment = self.parse_equipment(data.get('equipment'))
        self.actions = self.parse_actions(data.get('actions'))
        self.spells = self.parse_spells(data.get('spells'))
        self.traits = self.parse_traits(data.get('traits'))

        self.active_hooks = []
        self.stats = self.parse_stats(data.get('stats'))
        self.turn_stats = TurnStats()

        self.apply_equipment_and_passives()

        self.start_turn()

    def parse_info(self, data: dict) -> CharInfo:
        return CharInfo(**data)

    def parse_stats(self, data: dict) -> Stats:
        return Stats(**data)

    def parse_equipment(self, data: List[dict]) -> List[Equipment]:
        return [Equipment(**equip) for equip in data]

    def parse_actions(self, data: List[dict]) -> List[Action]:
        return [Action(**action) for action in data]

    def parse_spells(self, data: List[dict]) -> List[Spell]:
        return [Spell(**spell) for spell in data]

    def parse_traits(self, data: List[dict]) -> List[Trait]:
        return [Trait(**trait) for trait in data]

    def apply_equipment_and_passives(self):
        for equip in self.equipment:
            if equip.stat_plus is not None:
                self.stats.add_stats(equip.stat_plus)
            if equip.hooks is not None:
                for hook in equip.hooks:
                    self.hookhook(hook)

        passive_buffs = [
            buff for buff in self.spells + self.traits
            if buff.action_type == ActionTypes.passive]

        for buff in passive_buffs:
            for hook in buff.hooks:
                self.hookhook(hook)

    def use_action(self, action_index: int):
        action = self.actions[action_index]
        if action.category != ActionCategories.defense and self.pay_action('action', action.category):
            self.set_atk_n_roll_params(action.roll, attack_base_stat=action.base_stat, dmg_type=action.dmg_type,
                                       distance=action.distance)
            print(f"Using Action: {action.name}")
            self.call_on_attack_hooks(action.category)
            self.call_on_defense_hooks(action.category)
            self.turn_stats.current_roll = self.subs_base_stats(self.turn_stats.current_roll)
            print(self.turn_stats.current_roll)
            rl = rollroll(self.turn_stats.current_roll)
            self.reset_atk_n_roll_params()
            return rl
        else:
            self.set_atk_n_roll_params(action.roll)
            print(f"Using Action: {action.name}")
            self.call_on_defense_hooks(action.category)
            self.turn_stats.current_roll = self.subs_base_stats(self.turn_stats.current_roll)
            print(self.turn_stats.current_roll)
            rl = rollroll(self.turn_stats.current_roll)
            self.reset_atk_n_roll_params()
            return rl

    def use_spell(self, spell_index: int, trait=False):
        rl = None
        if trait is True:
            spell = self.traits[spell_index]
        else:
            spell = self.spells[spell_index]
        if spell.cur_uses > 0 and self.pay_action(spell.action_type, spell.category):
            spell.cur_uses -= 1
            print(f"Using Spell: {spell.name}")
            if spell.hooks is not None:
                for hook in spell.hooks:
                    self.hookhook(hook)
            if spell.category == ActionCategories.buff:
                pass
            elif spell.category == ActionCategories.action:
                if spell.roll is not None:
                    self.set_atk_n_roll_params(spell.roll, dmg_type=spell.dmg_type)
                    self.turn_stats.current_roll = self.subs_base_stats(self.turn_stats.current_roll)
                    print(self.turn_stats.current_roll)
                    rl = rollroll(self.turn_stats.current_roll)

            elif spell.category == ActionCategories.attack:
                self.set_atk_n_roll_params(spell.roll, dmg_type=spell.dmg_type)
                self.call_on_attack_hooks(spell.category)
                self.turn_stats.current_roll = self.subs_base_stats(self.turn_stats.current_roll)
                print(self.turn_stats.current_roll)
                rl = rollroll(self.turn_stats.current_roll)

            elif spell.category == ActionCategories.defense:
                self.set_atk_n_roll_params(spell.roll)
                self.call_on_defense_hooks(spell.category)
                self.turn_stats.current_roll = self.subs_base_stats(self.turn_stats.current_roll)
                print(self.turn_stats.current_roll)
                rl = rollroll(self.turn_stats.current_roll)

            if spell.test is not None:
                test = self.subs_base_stats(spell.test)
                print(f"O oponente faz um teste - {spell.test_description}: {test}")

        self.reset_atk_n_roll_params()
        return rl

    def use_trait(self, trait_index):
        return self.use_spell(trait_index, True)

    def damage(self, damage: int):
        self.set_damage_params(damage)
        self.call_on_damage_hooks()
        self.stats.current_hp -= self.turn_stats.due_damage
        if self.stats.current_hp < 1:
            print("died :v")
            for _ in range(3):
                sleep(1)
                print('.')
            sleep(1)
            while True:
                try:
                    hl = int(input("Hela to how much? "))
                    self.stats.current_hp = hl
                    break
                except ValueError:
                    print("Invalid input")

        self.reset_damage_params()

    def defend_for(self, damage: int, defend_item_idx: int = None, direct_damage: bool = False):
        if direct_damage:
            self.damage(damage)
        elif defend_item_idx:
            self.damage(damage - self.use_action(defend_item_idx))
        else:
            print(f'{defend_item_idx} idx not found')

    def subs_base_stats(self, roll: str):
        for stat_name, stat_value in self.stats.get_dict().items():
            roll = roll.replace(stat_name, str(stat_value))
        return roll

    def hookhook(self, hook: Hook):  # onhook calls
        if HookCallbacks.on_hook in hook.callbacks:
            hook.call(self)
        self.active_hooks.append(hook)

    def call_on_attack_hooks(self, category: str):
        if category == ActionCategories.attack:
            for hook in self.active_hooks:
                if HookCallbacks.on_attack in hook.callbacks:
                    hook.call(self)

    def call_on_defense_hooks(self, category: str):
        if category == ActionCategories.defense:
            for hook in self.active_hooks:
                if HookCallbacks.on_defense in hook.callbacks:
                    hook.call(self)

    def call_on_end_hooks(self, expired_hooks: List[Hook]):
        for hook in expired_hooks:
            if hook.duration < 1 and HookCallbacks.on_end in hook.callbacks:
                hook.call(self)

    def call_on_damage_hooks(self):
        for hook in self.active_hooks:
            if HookCallbacks.on_damage in hook.callbacks:
                hook.call(self)

    def pay_action(self, action_type: str, category: str):
        if category == ActionCategories.attack:
            if self.turn_stats.current_turn_extra_attack_qt > 0:
                self.turn_stats.current_turn_extra_attack_qt -= 1
                return True

        if action_type == ActionTypes.action:
            if self.turn_stats.current_turn_action_qt > 0:
                self.turn_stats.current_turn_action_qt -= 1
                return True
        elif action_type == ActionTypes.bonus_action:
            if self.turn_stats.current_turn_bonus_action_qt > 0:
                self.turn_stats.current_turn_bonus_action_qt -= 1
                return True
        elif action_type == ActionTypes.reaction:
            if self.turn_stats.current_turn_reaction_qt > 0:
                self.turn_stats.current_turn_reaction_qt -= 1
                return True
        else:
            return True
        print('Cannot Perform action')
        return False

    def set_atk_n_roll_params(self, roll: str, *, attack_base_stat: str = None,
                             dmg_type: str = None, distance: str = None):
        self.turn_stats.current_roll = copy(roll)
        self.turn_stats.current_attack_base_stat = attack_base_stat
        self.turn_stats.current_dmg_type = dmg_type
        self.turn_stats.current_distance = distance

    def reset_atk_n_roll_params(self):
        self.turn_stats.current_roll = ''
        self.turn_stats.current_attack_base_stat = None
        self.turn_stats.current_dmg_type = None
        self.turn_stats.current_distance = None

    def set_damage_params(self, damage: int):
        self.turn_stats.due_damage = damage

    def reset_damage_params(self):
        self.turn_stats.due_damage = 0

    def regain_all_spell_n_trait_uses(self):
        for spell in self.spells:
            spell.regain_uses()

    def end_turn(self):
        self.turn_stats._end_turn()

    def start_turn(self):
        expired_hooks_idxs = []
        for idx, hook in enumerate(self.active_hooks):
            hook.duration -= 1
            if hook.duration < 1:
                expired_hooks_idxs.append(idx)

        expired_hooks = [self.active_hooks.pop(idx) for idx in reversed(expired_hooks_idxs)]
        self.call_on_end_hooks(expired_hooks)

        self.turn_stats._start_turn()

    def print_info(self):
        print('\nInfo')
        print(
            f'name: {self.info.name}\n'
            f'level: {self.info.level}\n'
            f'exp: {self.info.exp}\n'
            f'karma: {self.info.karma}\n'
        )

    def print_stats(self, detailed: bool = False):
        print('\nStats')
        print(
            f'HP: {self.stats.current_hp}/{self.stats.MAX_HP} FOR:{self.stats.FOR} RES:{self.stats.RES} '
            f'INT:{self.stats.INT} SOR:{self.stats.SOR} CAR:{self.stats.CAR} VEL:{self.stats.VEL} '
            f'move_speed:{self.stats.move_speed}'
        )

    def print_turn_stats(self):
        print('\nTurn Stats')
        print(self.turn_stats)

    def print_equipment(self):
        print('\nEqupments')
        for idx, equip in enumerate(self.equipment):
            print(f'[{idx}] {equip}')

    def print_actions(self):
        print('\nActions')
        for idx, action in enumerate(self.actions):
            print(f'[{idx}] {action}')

    def print_spells(self, action_type_filter: str = None, category_filter: str = None):
        spells = {idx: val for idx, val in enumerate(copy(self.spells))}
        if action_type_filter is not None:
            spells = {idx: spell for idx, spell in spells.items() if spell.action_type == action_type_filter}
        if category_filter is not None:
            spells = {idx: spell for idx, spell in spells.items() if spell.category == category_filter}

        print('\nSpells')
        for idx, spell in spells.items():
            print(f'[{idx}] {spell}')

    def print_traits(self):
        print('\nTraits')
        for idx, trait in enumerate(self.traits):
            print(f'[{idx}] {trait}')

    def print_hooks(self):
        print('\nActive Hooks')
        for idx, hook in enumerate(self.active_hooks):
            print(f'[{idx}] {hook}')

    def print_all(self):
        self.print_info()
        self.print_stats()
        self.print_turn_stats()
        self.print_equipment()
        self.print_actions()
        self.print_spells()
        self.print_traits()
        self.print_hooks()

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def get(self, item):
        return self.__getitem__(item)

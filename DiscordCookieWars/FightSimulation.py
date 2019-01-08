import random
from copy import deepcopy
from math import ceil
import Unit


def attack(attack_troops, player_d):
    print("arrack against %s" % player_d.owner)
    # combine rallied units with defensive units
    player_d.clear_rallied()

    print("attacking: " + str(attack_troops))
    print("defending: " + str(player_d.units))

    attack_troops, player_d.units = simulate_fight(attack_troops, player_d.units, player_d.city_wall_health)
    print("after:")
    print("attackers" + str(attack_troops))
    print("defenders" + str(player_d.units))

    if attack_troops:  # the player one. (take the other persons resources)
        # calculate the loot the player will take
        capacity = sum([u.carrying_capacity * a for u, a in attack_troops.items()])
        per_resource = ceil(capacity // 4)  # at leas one

        overflow = 0  # the additional amount the use can carry of a resource if he can't carry the previous one
        loot = {}
        for r, a in player_d.resources.items():
            stolen = min(per_resource + overflow, a)
            player_d.resources[r] -= stolen
            loot[r] = stolen
            overflow = max(0, per_resource - stolen)

        # loot = deepcopy(player_d.resources)
        print("loot:")
        print(loot)
        for k, v in player_d.resources.items():
            player_d.resources[k] = 0
        return loot


def simulate_fight(p1, p2, city_wall_health):
    """simulates a fight between party 1 and party 2"""
    if not p2:  # if the defensive has no units
        return p1, p2

    # add city wall to p2_def units:
    p2_def = deepcopy(p2)
    cw_unit = Unit.Unit()
    cw_unit.health_list[1] = city_wall_health
    cw_unit.command_name = "city_wall"
    p2_def[cw_unit] = 1

    # calculate the total damage for both parties. the defender also has the city wall
    dmg1 = sum([adjusted_damage(u, amount, p2_def) for u, amount in p1.items()])
    dmg2 = sum([adjusted_damage(u, amount, p1) for u, amount in p2.items()])

    # calculate the other teams hp and then compare it to the damage made
    # this is slightly naive. the hp should be added as a proportion in the adjusted damage formular because being able
    # to kill other units faster is a bigger advantage because it also avoids damage (maybe for the beta)
    hp1 = sum([u.health * amount for u, amount in p1.items()])
    hp2 = sum([u.health * amount for u, amount in p2.items()])

    # the actual destruction done by p1 and p2 (damage per health)
    v1 = dmg1 / hp2
    v2 = dmg2 / hp1

    # killhp is the hp that the winner lost during the fight
    if v1 > v2:  # p1 won
        winner = p1
        kill_hp = v2 / v1 * hp1
        p2 = {}
    elif v2 > v1:  # p2 won
        winner = p2
        kill_hp = v1 / v2 * hp2
        p1 = {}
    else:
        p1 = {}
        p2 = {}

    # kill of some units of the winner according to the damage the looser made
    while kill_hp > 0:
        # calculate the probability of death for every type of unit
        death_prop = {1/unit.health * amount: unit for unit, amount in winner.items()}
        # choose what unit to kill
        ran_num = sum(death_prop.keys()) * random.random()
        for prop, unit in death_prop.items():
            if prop >= ran_num:
                # kill the unit
                winner[unit] -= 1
                if winner[unit] == 0:
                    del winner[unit]
                # adjust kill hp
                kill_hp -= unit.health
            else:
                # adjust ran_num
                ran_num -= prop
    return p1, p2


def adjusted_damage(attacker, amount, target_group):
    """does an evaluation of the potency of one type of attacker against the target group"""
    normal_damage = attacker.damage * amount

    # calculate the proportion of targets the unit is strong against. (proportion of the total health)
    # the sum of all units the attacker is strong against
    strong_amount = sum([amount * unit.health for unit, amount in target_group.items() if unit.command_name in attacker.strengths])
    p_effective = strong_amount / sum([amount * unit.health for unit, amount in target_group.items()])
    # this formula is derived by assuming all damage is done simultaneously. this means no units can die before making
    # all their potential damage. It still should be correct in most cases and more then suitable for this use case
    adj_dmg = (p_effective * (attacker.strength_damage_multiplier - 1) + 1) * normal_damage
    return adj_dmg

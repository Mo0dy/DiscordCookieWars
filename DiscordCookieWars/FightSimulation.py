import random


def simulate_fight(p1, p2):
    """simulates a fight between party 1 and party 2"""
    # calculate the total damage for both parties
    dmg1 = sum([adjusted_damage(u, amount, p2) for u, amount in p1.items()])
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

    # calculate the proportion of targets the unit is strong against
    # the sum of all units the attacker is strong against
    strong_amount = sum([amount for unit, amount in target_group.items() if unit.command_name in attacker.strengths])
    p_effective = strong_amount / sum(target_group.values())
    # this formula is derived by assuming all damage is done simultaneously. this means no units can die before making
    # all their potential damage. It still should be correct in most cases and more then suitable for this use case
    adj_dmg = (p_effective * (attacker.strength_damage_multiplier - 1) + 1) * normal_damage
    return adj_dmg


if __name__ == "__main__":
    from Unit import *
    p1 = {
        Archer(): 9,
        Soldier(): 1,
    }
    p2 = {
        Archer(): 1,
        Soldier(): 9,
    }
    p1, p2 = simulate_fight(p1, p2)
    print(p1, p2)


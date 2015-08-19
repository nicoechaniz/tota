from random import choice
import settings
from tota.utils import distance, adjacent_positions, closest, sort_by_distance, adjacent_positions, possible_moves
from tota.actions import calculate_damage
from random import choice
from tota.things import Hero

from syslog import syslog

AUTHOR = "nicoechaniz"

# avoid trees and towers
def valid_positions(me, things):
    return [position for position in adjacent_positions(me) if things.get(position) == None
            or (hasattr(things.get(position), "name") and things.get(position).name not in ["tree", "tower"])]

def log(txt, t):
    pass
#    return syslog("%s: %s" % (str(t), str(txt)))

def safe_fireball(hero, enemy, closest_friend, t):
    enemy_distance = distance(hero, enemy)
    if hero.can('fireball', t) and enemy_distance <= settings.FIREBALL_DISTANCE\
       and enemy_distance > settings.FIREBALL_RADIUS\
       and distance(closest_friend, enemy) > settings.FIREBALL_RADIUS:
        return True
    else:
        return False

def create():

    def rush_hero_logic(self, things, t):
        enemy_team = settings.ENEMY_TEAMS[self.team]
        enemies = [thing for thing in things.values()
                   if thing.team == enemy_team]
        closest_enemy = closest(self, enemies)
        closest_enemy_distance = distance(self, closest_enemy)

        enemy_ancient = [e for e in enemies if e.name == 'ancient'][0]

        enemy_tower = None
        enemy_tower = [e for e in enemies if e.name == 'tower']
        if enemy_tower: enemy_tower = enemy_tower[0]

        enemy_hero = None
        enemy_heroes = [e for e in enemies if isinstance(e, Hero)]
        if enemy_heroes: enemy_hero = closest(self, enemy_heroes)

        friends = [thing for thing in things.values()
                   if thing.team == self.team and thing != self]
        friendly_ancient = [e for e in friends if e.name == 'ancient'][0]
        back_friends = sort_by_distance(self, friends)[2:]
        closest_friend = closest(self, friends)
        closest_friend_distance = distance(self, closest_friend)
        
        full_path_distance = distance(enemy_ancient, friendly_ancient)

        offside = closest(enemy_ancient, back_friends + [self]) == self 

        # enemy units behind me
        enemy_offside = closest(friendly_ancient, enemies + [self]) != self 

        # if I can stun the other hero, that's highest priority
        if closest_enemy and closest_enemy == enemy_hero\
           and closest_enemy_distance <= settings.STUN_DISTANCE and self.can('stun', t):
            # try to stun him
            log('stun !!!', t)
            return 'stun', closest_enemy.position

        surrounding_damage = 0
        heal_effect = calculate_damage(self, settings.HEAL_BASE_HEALING, settings.HEAL_LEVEL_MULTIPLIER)
        heal_targets = [ f for f in friends + [self] \
                         if distance(self, f) <= settings.HEAL_RADIUS ]
        for friend in heal_targets:
            surrounding_damage += friend.max_life - friend.life
            
        # maximize heal effect
        if self.can('heal', t) and surrounding_damage >= heal_effect:
            log("heal", t)
            return 'heal', self.position

        # if I'm at the enemy ancient, prioritize attacking it
        if closest_enemy and closest_enemy == enemy_ancient\
           and distance(self, closest_enemy) <= settings.HERO_ATTACK_DISTANCE:
            fireball_damage = calculate_damage(self, settings.FIREBALL_BASE_DAMAGE, settings.FIREBALL_LEVEL_MULTIPLIER)
            if self.can('fireball', t) and enemy_ancient.life <= fireball_damage:
                log('FIREBALL FINISH!!!!!!!!!!!', t)
                return 'fireball', closest_enemy.position
            else:
                return 'attack', closest_enemy.position

        rush_trigger = max([200, self.max_life/2])
        # get cover if I'm low on energy
        if offside and self.life < rush_trigger:
            moves = sort_by_distance(friendly_ancient, valid_positions(self, things))
            return 'move', moves[0]


        if enemies:
            if enemy_tower and safe_fireball(self, enemy_tower, closest_friend, t):
                # fireball the tower if in range
                log("fireball TOWER !!!", t)
                return 'fireball', enemy_tower.position
            else:
                fball_targets = [ e for e in enemies\
                                  if distance(self, e) <= settings.FIREBALL_DISTANCE ]
                fball_friendlies = [ f for f in friends\
                                     if distance(self, f) <= settings.FIREBALL_DISTANCE ]
                if fball_targets:
                    # choose the furthest enemy within fireball range
                    best_fball_target = sort_by_distance(self, fball_targets)[-1]
                    if safe_fireball(self, best_fball_target, closest_friend, t):
                        log("fireball", t)
                        return 'fireball', best_fball_target.position

            if closest_enemy_distance <= settings.HERO_ATTACK_DISTANCE:
#                log("attack", t)
                return 'attack', closest_enemy.position

            else:
                if enemy_tower:
                    if distance(self,enemy_tower) < settings.FIREBALL_DISTANCE:
                        log("halt", t)
                        return

                moves = sort_by_distance(enemy_ancient, valid_positions(self, things))                        

                return 'move', moves[0]

    return rush_hero_logic

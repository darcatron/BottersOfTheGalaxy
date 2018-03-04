import random
import sys
import math

### CONSTANTS
INSULTS = ["come at me", "who's your daddy", "is this LoL", "cash me outside", "2 + 2 don't know what it is!", "yawn",
           "dis some disrespect"]
FINAL_INSULT = "2 ez. gg. no re"

HERO_DEADPOOL = "DEADPOOL"

ENTITY_TYPE_MINION = "UNIT"
ENTITY_TYPE_HERO = "HERO"
ENTITY_TYPE_TOWER = "TOWER"

ACTION_WAIT = "WAIT"
ACTION_MOVE = "MOVE"
ACTION_ATTACK = "ATTACK"
ACTION_ATTACK_NEAREST = "ATTACK_NEAREST"
ACTION_MOVE_ATTACK = "MOVE_ATTACK"
ACTION_BUY = "BUY"
ACTION_SELL = "SELL"

### Globals
curInsult = ""
myTeam = None
allEntities = []

def play():
    global myTeam, allEntities
    myTeam = int(raw_input())

    unused()

    itemCount = int(raw_input())  # useful from wood2
    readInItems(itemCount)
    curTurn = 1

    # game loops
    while True:
        gold = int(raw_input())
        enemyGold = int(raw_input())
        roundType = int(raw_input())  # a positive value will show the number of heroes that await a command

        if roundType < 0:
            chooseHero()

        entityCount = int(raw_input())
        readInEntities(entityCount)

        # If roundType has a negative value then you need to output a Hero name, such as "DEADPOOL" or "VALKYRIE".
        # Else you need to output roundType number of any valid action, such as "WAIT" or "ATTACK unitId"
        if roundType > 0:
            executeTurn(curTurn, gold)
            curTurn += 1


def executeTurn(curTurn, gold):
    otherTeam = getOtherTeam(myTeam)

    # Hide behind our minions
    shieldMinion = findMinionForBodyShield(myTeam)

    # Find closest enemy minion to attack
    myHero = getHero(myTeam)

    ## TODO find the closest entity to the spot we will move to! Not where we are currently, since we move before attacking
    minionToAttack = findClosestEntity(getMinions(otherTeam), myHero.posX, myHero.posY)

    myTower = getTower(myTeam)

    itemName = getMostAffordableDamageOrMoveItemName(gold)

    if itemName is not None and curTurn <= 4:
        printMove(ACTION_BUY + " " + itemName, curTurn)
    elif shieldMinion is not None:
        if minionToAttack is not None:
            printMove(ACTION_MOVE_ATTACK + " " + str(shieldMinion.posX) + " " + str(shieldMinion.posY) + " " + str(minionToAttack.unitId), curTurn)
        else:
            printMove(ACTION_MOVE + " " + str(shieldMinion.posX) + " " + str(shieldMinion.posY), curTurn)
    else:
        # We don't have a shield minion so we should move towards tower
        printMove(ACTION_MOVE + " " + str(myTower.posX) + " " + str(myTower.posY), curTurn)

# Use to buy an item with damage being priority and moveSpeed taking second, this will return an itemName
# or None if neither are affordable
def getMostAffordableDamageOrMoveItemName(gold):
    damageItems = [i for i in allItems if "blade" in i.itemName.lower()]
    moveSpeedItems = [i for i in allItems if "boots" in i.itemName.lower()]
    itemName = None

    # Check for affordable items that raise damage first
    for item in damageItems:
        if item.itemCost <= gold:
            itemName = item.itemName
            break

    # If no affordable items that raise damage then check for items that raise moveSpeed
    if itemName is None:
        for item in moveSpeedItems:
            if item.itemCost <= gold:
                itemName = item.itemName

    return itemName

## Use to decide whether to add or subtract for the X direction
def getDirectionMultiplier(team):
    return 1 if team == 0 else -1


## Returns true if entity 1 is closer to the given team's tower than entity 2 is
def isCloserToTower(entity1, entity2, team):
    tower = getTower(team)
    entity1Distance = abs(getDistanceBetweenEntities(tower, entity1))
    entity2Distance = abs(getDistanceBetweenEntities(tower, entity2))

    return entity1Distance < entity2Distance


## NOTE this is the X direction ONLY
## Will return negative value if entity1 is farther left than entity 2 (otherwise positive)
def getDistanceBetweenEntities(entity1, entity2):
    return entity1.posX - entity2.posX


## Finds the entity farthest from the given coordinates.
def findFarthestEntity(entities, x=None, y=None):
    if x is None and y is None:
        raise ValueError("either x or y must be provided to findFarthestEntity()")

    maxDist = None
    farthestEntity = None

    for e in entities:
        dist = getDistanceBetweenPoints(e.posX, e.posY, x, y)

        if maxDist is None or dist > maxDist:
                farthestEntity = e
                maxDist = dist

    return farthestEntity


## Finds the entity closest to the given coordinates
def findClosestEntity(entities, x=None, y=None):
    if x is None and y is None:
        raise ValueError("either x or y must be provided to findClosestEntity()")

    minDist = None
    closestEntity = None

    for e in entities:
        dist = getDistanceBetweenPoints(e.posX, e.posY, x, y)

        if minDist is None or dist < minDist:
                closestEntity = e
                minDist = dist

    return closestEntity


## NOTE: This is absolute value! Doesn't take direction into account at all
## If only x is provided, only takes x into account. Same thing for y
## If both x and y are provided it calculates the hypotenuse
def getDistanceBetweenPoints(x1=None, y1=None, x2=None, y2=None):
    xDist = None
    yDist = None

    if x1 is not None and x2 is not None:
        xDist = abs(x1 - x2)
    elif y1 is not None and y2 is not None:
        yDist = abs(y1 - y2)
    else:
        raise ValueError("either x or y must be provided to getDistanceBetweenPoints()")

    if xDist is not None and yDist is not None:
        return math.sqrt(xDist * xDist + yDist * yDist)
    elif xDist is not None:
        return xDist
    else:
        return yDist


def findMinionForBodyShield(team):
    minions = getMinions(team)
    tower = getTower(team)

    healthyMinions = [m for m in minions if not isLowHealth(m)]

    ## Look for a healthy minion first because we need a good body shield!
    ## NOTE that for now we look at the X direction ONLY when computing distance
    bodyShieldMinion = findFarthestEntity(healthyMinions, tower.posX)
    if bodyShieldMinion is None:
        oppositeTower = getTower(getOtherTeam(team))
        ## We don't have any healthy minions! Retreat to minion farthest from OPPOSITE tower
        bodyShieldMinion = findFarthestEntity(minions, oppositeTower.posX)

    return bodyShieldMinion


def isLowHealth(entity):
    if entity.maxHealth <= 0:
        return True

    lowHealthPercentage = 25
    return entity.health / entity.maxHealth < (entity.maxHealth * (lowHealthPercentage / 100))

def getHero(team):
    for entity in allEntities:
        if isinstance(entity, Hero) and entity.team == team:
            return entity

    raise ValueError("Missing hero for team " + team)


def getTower(team):
    for entity in allEntities:
        if isinstance(entity, Tower) and entity.team == team:
            return entity

    raise ValueError("Missing tower for team " + team)


def getMinions(team):
    ourMinions = []
    for entity in allEntities:
        if isinstance(entity, Minion) and entity.team == team:
            ourMinions.append(entity)

    return ourMinions


def getOtherTeam(team):
    if team == 0:
        return 1
    else:
        return 0

def readInEntities(entityCount):
    global allEntities
    allEntities = []

    for i in range(entityCount):
        # unitType: UNIT, HERO, TOWER, can also be GROOT from wood1
        # shield: useful in bronze
        # stunDuration: useful in bronze
        # countDown1: all countDown and mana variables are useful starting in bronze
        # heroType: DEADPOOL, VALKYRIE, DOCTOR_STRANGE, HULK, IRONMAN
        # isVisible: 0 if it isn't
        # itemsOwned: useful from wood1
        unitId, team, entityType, x, y, attackRange, health, maxHealth, shield, attackDamage, movementSpeed, stunDuration, goldValue, countDown1, countDown2, countDown3, mana, maxMana, manaRegeneration, heroType, isVisible, itemsOwned = raw_input().split()
        unitId = int(unitId)
        team = int(team)
        x = int(x)
        y = int(y)
        attackRange = int(attackRange)
        health = int(health)
        maxHealth = int(maxHealth)
        shield = int(shield)
        attackDamage = int(attackDamage)
        movementSpeed = int(movementSpeed)
        stunDuration = int(stunDuration)
        goldValue = int(goldValue)
        countDown1 = int(countDown1)
        countDown2 = int(countDown2)
        countDown3 = int(countDown3)
        mana = int(mana)
        maxMana = int(maxMana)
        manaRegeneration = int(manaRegeneration)
        isVisible = int(isVisible)
        itemsOwned = int(itemsOwned)

        entity = None
        if entityType == ENTITY_TYPE_MINION:
            entity = Minion(unitId, team, x, y, attackRange, health, maxHealth, attackDamage, movementSpeed)
        elif entityType == ENTITY_TYPE_HERO:
            entity = Hero(heroType, unitId, team, x, y, attackRange, health, maxHealth, mana, maxMana,
                          attackDamage, movementSpeed, manaRegeneration, isVisible, itemsOwned)
        elif entityType == ENTITY_TYPE_TOWER:
            entity = Tower(unitId, team, x, y)

        if entity is None:
            raise ValueError("unknown entity type " + entityType)

        allEntities.append(entity)


def chooseHero():
    print HERO_DEADPOOL

def unused():
    bushAndSpawnPointCount = int(raw_input())  # useful from wood1, represents the number of bushes and the number of places where neutral units can spawn
    for i in range(bushAndSpawnPointCount):
        # entityType: BUSH, from wood1 it can also be SPAWN
        entityType, x, y, radius = raw_input().split()
        x = int(x)
        y = int(y)
        radius = int(radius)

def readInItems(itemCount):
    global allItems
    allItems = []

    for i in range(itemCount):
        # itemName: contains keywords such as BRONZE, SILVER and BLADE, BOOTS connected by "" to help you sort easier
        # itemCost: BRONZE items have lowest cost, the most expensive items are LEGENDARY
        # damage: keyword BLADE is present if the most important item stat is damage
        # moveSpeed: keyword BOOTS is present if the most important item stat is moveSpeed
        # isPotion: 0 if it's not instantly consumed
        itemName, itemCost, damage, health, maxHealth, mana, maxMana, moveSpeed, manaRegeneration, isPotion = raw_input().split()
        itemCost = int(itemCost)
        damage = int(damage)
        health = int(health)
        maxHealth = int(maxHealth)
        mana = int(mana)
        maxMana = int(maxMana)
        moveSpeed = int(moveSpeed)
        manaRegeneration = int(manaRegeneration)
        isPotion = int(isPotion)

        item = Item(itemName, itemCost, damage, health, maxHealth, mana, maxMana, moveSpeed, manaRegeneration, isPotion)
        allItems.append(item)

def printMove(move, turn):
    global curInsult

    # update insult every 10 turns
    if turn % 10 == 0:
        curInsult = random.choice(INSULTS)

    # Write an action using print
    print move + ";" + curInsult


def debug(objOrStr):
    if isinstance(objOrStr, Entity):
        print >> sys.stderr, objOrStr.__dict__
    elif isinstance(objOrStr, list):
        debug("[")
        for el in objOrStr:
            debug(el)
        debug("]")
    else:
        print >> sys.stderr, objOrStr

########################################################################################################################
########################################################################################################################
################################################## Classes #############################################################
########################################################################################################################
########################################################################################################################

class Entity(object):

    def __init__(self, unitId, entityType, team, posX, posY, attackRange, health, maxHealth, mana, maxMana, attackDamage, movementSpeed):
        self.unitId = unitId
        self.entityType = entityType
        self.team = team
        self.posX = posX
        self.posY = posY
        self.attackRange = attackRange
        self.health = health
        self.maxHealth = maxHealth
        self.mana = mana
        self.maxMana = maxMana
        self.attackDamage = attackDamage
        self.movementSpeed = movementSpeed

class Minion(Entity):

    def __init__(self, unitId, team, posX, posY, attackRange, health, maxHealth, attackDamage, movementSpeed, mana=0, maxMana=0):
        super(Minion, self).__init__(unitId, ENTITY_TYPE_MINION, team, posX, posY, attackRange, health, maxHealth, mana, maxMana,
                                     attackDamage, movementSpeed)

class Hero(Entity):

    def __init__(self, heroType, unitId, team, posX, posY, attackRange, health, maxHealth, mana, maxMana, attackDamage, movementSpeed, manaRegeneration, isVisible, itemsOwned):
        super(Hero, self).__init__(unitId, ENTITY_TYPE_HERO, team, posX, posY, attackRange, health, maxHealth,
                                   mana, maxMana, attackDamage, movementSpeed)

        self.heroType = heroType
        self.manaRegeneration = manaRegeneration
        self.isVisible = isVisible
        self.itemsOwned = itemsOwned


class Tower(Entity):

    def __init__(self, unitId, team, posX, posY):
        super(Tower, self).__init__(unitId, ENTITY_TYPE_TOWER, team, posX, posY, attackRange=400, health=3000, maxHealth=3000,
                                    mana=0, maxMana=0, attackDamage=100, movementSpeed=0)

class Item(object):

    def __init__(self, itemName, itemCost, damage, health, maxHealth, mana, maxMana, moveSpeed, manaRegeneration, isPotion):
        self.itemName = itemName
        self.itemCost = itemCost
        self.damage = damage
        self.health = health
        self.maxHealth = maxHealth
        self.mana = mana
        self.maxMana = maxMana
        self.moveSpeed = moveSpeed
        self.manaRegeneration = manaRegeneration
        self.isPotion = isPotion

play()

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId


class FourGateBot(BotAI):

    ### FUNCTIONS ###
    async def warp_new_units(self, location):
        for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if AbilityId.WARPGATETRAIN_STALKER in abilities:
                pos = location.position.to2.random_on_distance(4)
                placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
                if placement is None:
                    # return ActionResult.CantFindPlacementLocation
                    logger.info("can't place")
                    return
                warpgate.warp_in(UnitTypeId.STALKER, placement)

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("I Will Four Gate You")
        await self.distribute_workers()

        ### GENERAL ###
        # sets first nexus
        nexus = self.townhalls.first

        print("SUPPLY USED")
        print(self.supply_used)

        # Make probes until 22
        if self.supply_workers < 22 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        if not self.townhalls:
            ## Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        # Research WarpGate
        if (
                self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(AbilityId.RESEARCH_WARPGATE)
                and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
        ):
            ccore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            ccore.research(UpgradeId.WARPGATERESEARCH)




        ### after build order ###

        if self.supply_used > 25 and self.supply_left < 2 and self.already_pending(UnitTypeId.PYLON) == 0:
            ## Always check if you can afford something before you build it
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.enemy_start_locations[0], 15))
            return

        # Make stalkers attack either closest enemy unit or enemy spawn location
        if self.units(UnitTypeId.STALKER).amount > 6:
            for stalker in self.units(UnitTypeId.STALKER).ready.idle:
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(stalker)
                    stalker.attack(target)
                else:
                    stalker.attack(self.enemy_start_locations[0])



        ### warp in units
        if self.structures(UnitTypeId.WARPGATE).amount > 1:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            await self.warp_new_units(pylon)





        ### PROCEDURAL ###

        ## SUPPlY 14

        if self.supply_used == 14 and self.already_pending(UnitTypeId.PYLON) == 0:
            pos = nexus.position.towards(self.enemy_start_locations[0], 15)
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=pos)

        ## SUPPLY 15
        if self.supply_used == 15:
            if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                nexuses = self.structures(UnitTypeId.NEXUS)
                abilities = await self.get_available_abilities(nexuses)
                for loop_nexus, abilities_nexus in zip(nexuses, abilities):
                    if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                        loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                        break

        ## SUPPLY 16

        if self.supply_used == 16:
            firstPylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.can_afford(UnitTypeId.GATEWAY) and self.already_pending(UnitTypeId.GATEWAY) < 1:
                await self.build(UnitTypeId.GATEWAY, near=firstPylon)

        if self.supply_used >= 16 and self.already_pending(UnitTypeId.GATEWAY):
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build(UnitTypeId.ASSIMILATOR, vg)
                    worker.stop(queue=True)

        ## SUPPLY 17
        if self.supply_used >= 17 and self.already_pending(UnitTypeId.GATEWAY) == 1 and self.structures(UnitTypeId.GATEWAY).amount==1 :
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.can_afford(UnitTypeId.GATEWAY):
                await self.build(UnitTypeId.GATEWAY, near=pylon)

        if self.supply_used >= 17 and self.structures(UnitTypeId.GATEWAY).ready.amount >= 1 and self.structures(UnitTypeId.CYBERNETICSCORE).amount < 1:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.can_afford(UnitTypeId.CYBERNETICSCORE) and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

        ## SUPPLY 21
        if self.supply_used == 21 and self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.enemy_start_locations[0], 15))

        ##SUPPLY 22
        if self.supply_used >= 22 and self.structures(UnitTypeId.CYBERNETICSCORE).ready.amount == 1:
            for gt in self.structures(UnitTypeId.GATEWAY).ready.idle:
                if self.can_afford(UnitTypeId.STALKER):
                    gt.train(UnitTypeId.STALKER)

        ##SUPPLY 25
        if self.supply_used == 22 and self.already_pending(UnitTypeId.GATEWAY) < 2:
            if self.can_afford(UnitTypeId.GATEWAY):
                await self.build(UnitTypeId.GATEWAY, near=nexus.position.towards(self.enemy_start_locations[0], 15))



############
##############
##########
if __name__ == "__main__":
    run_game(maps.get("AcropolisLE"), [
        Bot(Race.Protoss, FourGateBot()),
        Computer(Race.Zerg, Difficulty.Hard)
    ], realtime=True)

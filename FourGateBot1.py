from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId

import random


class FourGateBot(BotAI):

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("Maplez is a clown")
        await self.distribute_workers()


        if not self.townhalls:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return
        else:
            nexus = self.townhalls.random

        # make probes until we have 24
        if self.supply_workers < 22 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        if self.supply_used >= 14 and self.structures(UnitTypeId.PYLON).amount == 0:

            nexus = self.townhalls.random
            pos = nexus.position.towards(self.enemy_start_locations[0], 15)

            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=pos)

        if self.supply_used >= 15:
            if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                nexuses = self.structures(UnitTypeId.NEXUS)
                abilities = await self.get_available_abilities(nexuses)
                for loop_nexus, abilities_nexus in zip(nexuses, abilities):
                    if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                        loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                        break
        if self.structures(UnitTypeId.PYLON).ready:
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.structures(UnitTypeId.GATEWAY).ready:
                # If we have gateway completed, build cyber core
                if not self.structures(UnitTypeId.CYBERNETICSCORE):
                    if (
                            self.can_afford(UnitTypeId.CYBERNETICSCORE)
                            and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
                    ):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
            else:

                # If we have no gateway, build gateway
                if self.can_afford(UnitTypeId.GATEWAY) and self.already_pending(UnitTypeId.GATEWAY) < 2:
                    await self.build(UnitTypeId.GATEWAY, near=pylon)

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



        if self.supply_used >= 21 and self.structures(UnitTypeId.PYLON).amount <= 2:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=self.structures(UnitTypeId.GATEWAY))



        # random nexus chronoboost gogo
        if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and self.supply_used == 14:
            nexuses = self.structures(UnitTypeId.NEXUS)
            abilities = await self.get_available_abilities(nexuses)
            for loop_nexus, abilities_nexus in zip(nexuses, abilities):
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                    loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                    break


        if self.structures(UnitTypeId.CYBERNETICSCORE).ready.idle:
            for cyber in UnitTypeId.CYBERNETICSCORE:
                if self.can_afford(UnitTypeId.WARPGATE):
                    self.research(UnitTypeId.WARPGATE)

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready.idle:
            for gt in self.structures(UnitTypeId.GATEWAY).ready.idle:
                if self.can_afford(UnitTypeId.STALKER):
                    await gt.train(UnitTypeId.STALKER)

        # If we have no pylon, build one near the nexus




############
##############
##########


run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, FourGateBot()),
    Computer(Race.Protoss, Difficulty.Medium)
], realtime=False)

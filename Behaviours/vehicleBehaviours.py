from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json
import asyncio # <--- Importar asyncio
import random  # <--- Importar random

class AnnouncePresenceBehaviour(OneShotBehaviour):
    """Comportamento para um veículo normal anunciar presença ao semáforo após um delay."""

    def __init__(self, delay, **kwargs): # <--- Adicionar parâmetro delay
        super().__init__(**kwargs)
        self.delay = delay # <--- Guardar o delay

    async def run(self):
        await asyncio.sleep(self.delay) # <--- Adicionar sleep AQUI

        target_tl_jid = self.agent.get("target_traffic_light_jid")
        #print(f"Veículo {self.agent.jid}: Anunciando presença para {target_tl_jid} após {self.delay:.1f}s")
        msg = Message(to=target_tl_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "vehicle_presence")
        msg.body = json.dumps({"vehicle_type": "normal"})
        await self.send(msg)
        await self.agent.stop()

class AnnounceEmergencyBehaviour(OneShotBehaviour):
    """Comportamento para um veículo de emergência anunciar alerta ao semáforo após um delay."""

    def __init__(self, delay=0.5, **kwargs): # <--- Adicionar parâmetro delay (default 0.5s)
        super().__init__(**kwargs)
        self.delay = delay # <--- Guardar o delay

    async def run(self):
        await asyncio.sleep(self.delay) # <--- Adicionar sleep AQUI

        target_tl_jid = self.agent.get("target_traffic_light_jid")
        print(f"EMERGÊNCIA {self.agent.jid}: Enviando ALERTA para {target_tl_jid} após {self.delay:.1f}s")
        msg = Message(to=target_tl_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "emergency_alert")
        msg.body = json.dumps({"vehicle_type": "emergency"})
        await self.send(msg)
        await self.agent.stop()
from spade.behaviour import OneShotBehaviour
from spade.message import Message
import json
import asyncio
import random 

class AnnouncePresenceBehaviour(OneShotBehaviour):
    """Comportamento para um veículo normal anunciar presença ao semáforo após um delay."""

    def __init__(self, delay, **kwargs): 
        super().__init__(**kwargs)
        self.delay = delay 

    async def run(self):
        await asyncio.sleep(self.delay) 

        target_tl_jid = self.agent.get("target_traffic_light_jid")
        
        msg = Message(to=target_tl_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "vehicle_presence")
        msg.body = json.dumps({
            "vehicle_type": "normal",
            "vehicle_jid": str(self.agent.jid)
        })
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
        
class WaitForPermissionBehaviour(OneShotBehaviour):
    async def run(self):
        #print(f"{self.agent.jid}: À espera de permissão...")

        while True:
            msg = await self.receive(timeout=5)
            if msg and msg.metadata.get("protocol") == "go_ahead":
                
                # Recbeu verde e agora está à espera o tempo de passagem
                data = json.loads(msg.body)
                waiting_time = data.get("waiting_time", 0)
                print(f"{self.agent.jid}: Vai esperar {waiting_time}s antes de atravessar...")
                await asyncio.sleep(waiting_time)
                
                # aqui volta a verificar se ainda está verde na sua vez
                query_msg = Message(to=self.agent.target_traffic_light_jid)
                query_msg.set_metadata("performative", "request")
                query_msg.set_metadata("protocol", "traffic_light_state")
                query_msg.body = "Qual o teu estado atual?"
                await self.send(query_msg)

                # Enviar confirmação de passagem
                response = await self.receive(timeout=5)
                
                if response and response.metadata.get("protocol") == "traffic_light_state_reply":
                    state = json.loads(response.body).get("state")
                    
                    if state == "GREEN":
                        # Atravessa
                        notify_msg = Message(to=self.agent.target_traffic_light_jid)
                        notify_msg.set_metadata("performative", "inform")
                        notify_msg.set_metadata("protocol", "vehicle_passed")
                        notify_msg.body = json.dumps({"status": "passed"})
                        await self.send(notify_msg)

                        print(f"{self.agent.jid}: ✅ Semáforo está verde, a atravessar.")
                        await self.agent.stop()
                    else:
                        print(f"{self.agent.jid}: ⚠️ Semáforo não está verde ({state}). Vai aguardar nova ordem.")
                else:
                    print(f"{self.agent.jid}: ❌ Sem resposta do semáforo.")

            await asyncio.sleep(1)
        

from spade.agent import Agent
from Behaviours.vehicleBehaviours import AnnounceEmergencyBehaviour
# import asyncio # Já não é preciso aqui

class EmergencyVehicleAgent(Agent):
    """
    Agente 'dummy' que representa um veículo de emergência.
    Envia uma mensagem de alerta para o semáforo alvo.
    """
    async def setup(self):
        print(f"Agente Emergência {self.jid} a iniciar...")
        target_tl_jid = self.get("target_traffic_light_jid")
        if not target_tl_jid:
            print(f"EMERGÊNCIA {self.jid} ERRO: Não foi definido um semáforo alvo!")
            return

        # Anuncia com o delay default (0.5s) definido no __init__ do behaviour
        # ou passa um valor específico: AnnounceEmergencyBehaviour(delay=1.0)
        self.add_behaviour(AnnounceEmergencyBehaviour()) # <--- SEM start_at, pode passar delay opcional
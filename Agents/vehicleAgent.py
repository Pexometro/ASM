from spade.agent import Agent
from Behaviours.vehicleBehaviours import AnnouncePresenceBehaviour, WaitForPermissionBehaviour
# import asyncio # Já não é preciso aqui
import random

class VehicleAgent(Agent):
    """
    Agente 'dummy' que representa um veículo normal.
    Apenas envia uma mensagem para o semáforo alvo a indicar presença.
    """
    
    async def setup(self):

        self.target_traffic_light_jid = self.get("target_traffic_light_jid")
        
        if not self.target_traffic_light_jid:
            print(f"VEÍCULO {self.jid} ERRO: Não foi definido um semáforo alvo!")
            return

        # Define um delay aleatório
        delay = random.uniform(1, 10)
        #print(f"Veículo {self.jid} vai anunciar presença em {delay:.1f} segundos.")

        # Cria o comportamento passando o delay, SEM start_at
        self.add_behaviour(AnnouncePresenceBehaviour(delay=delay))
        self.add_behaviour(WaitForPermissionBehaviour())


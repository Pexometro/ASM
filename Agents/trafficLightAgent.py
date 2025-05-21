from spade.agent import Agent
from spade.template import Template
from Behaviours.trafficLightBehaviours import ReceiveCommandsBehaviour, ReceiveVehicleInfoBehaviour, ReportStatusBehaviour, SendGoAheadBehaviour
from spade.behaviour import OneShotBehaviour
import random
from spade.message import Message
import asyncio
import json

class TrafficLightAgent(Agent):
    """
    Agente que representa um semáforo.
    Recebe comandos do coordenador, deteta veículos (via mensagem),
    e reporta o estado/tráfego.
    """
    def __init__(self, jid, password, light_id, passadeira, oposto, **kwargs):
        super().__init__(jid, password, **kwargs)
        self.light_id = light_id # ID único para o semáforo (ex: "TL_1")
        self.current_state = "RED" # Estado inicial
        self.vehicles_queue = []
        self.coordinator_jid = None # Será definido no setup
        self.passadeira = passadeira 
        self.oposto = oposto

    async def setup(self):
        print(f"Agente Semáforo {self.jid} ({self.light_id}) a iniciar...")
        self.coordinator_jid = self.get("coordinator_jid")
        if not self.coordinator_jid:
            print(f"ERRO FATAL: Semáforo {self.jid} não recebeu o JID do coordenador!")
            # Considerar parar o agente aqui
            return

        # Comportamento para receber comandos do Coordenador
        cmd_template = Template()
        cmd_template.set_metadata("performative", "request") # Ouve por 'request'
        cmd_template.sender = self.coordinator_jid # Ouve apenas do coordenador
        self.add_behaviour(ReceiveCommandsBehaviour(), cmd_template)

        # Comportamento para receber info de Veículos (normais e emergência)
        # Ouve por 'inform' de qualquer veículo
        vehicle_info_template = Template()
        self.add_behaviour(ReceiveVehicleInfoBehaviour(), vehicle_info_template)
        # Adicionar filtro por protocolo se necessário (ex: "vehicle_presence", "emergency_vehicle")

        # Comportamento periódico para reportar estado/tráfego ao Coordenador
        # Reporta a cada 4 segundos (um pouco antes da lógica do coordenador)
        self.add_behaviour(ReportStatusBehaviour(period=4))
        
        

        print(f"Agente Semáforo {self.jid} ({self.light_id}) configurado. Estado inicial: {self.current_state}")

    async def set_state(self, new_state, duration=None):
        """Atualiza o estado do semáforo e imprime a mudança."""
        if self.current_state != new_state:
            if new_state == "RED":
                if self.current_state == "GREEN":
                    self.current_state = "YELLOW"
                    print(f"--- SEMÁFORO {self.light_id}: MUDOU PARA AMARELO ---")
                    await asyncio.sleep(5)
                    self.current_state = "RED"
                    print(f"--- SEMÁFORO {self.light_id}: MUDOU PARA VERMELHO ---")
                elif self.current_state != "RED":
                    # Se estiver em YELLOW (transição já em curso) ou outro estado inesperado
                    await asyncio.sleep(1)
                    self.current_state = "RED"
                    print(f"--- SEMÁFORO {self.light_id}: Forçado a VERMELHO ---")
                
            elif new_state == "GREEN":
                print(f"--- SEMÁFORO {self.light_id} ({self.jid}): RECEBEU O COMANDO E VAI AGUARDAR 5 SEGUNDOS PARA MUDAR PARA VERDE ---")
                await asyncio.sleep(5) 
                
                self.current_state = "GREEN"
                                
                self.emptying_task = asyncio.create_task(self.notify_waiting_vehicles())
                
                
    def increment_vehicle_count(self):
        """Incrementa a contagem de veículos."""
        self.vehicle_count += 1
        #print(f"TL {self.light_id}: Veículo detectado. Contagem atual: {self.vehicle_count}")

    async def notify_waiting_vehicles(self):

        for idx, vehicle_jid in enumerate(self.vehicles_queue):
            waiting_time = idx * 2  
            behaviour = SendGoAheadBehaviour(vehicle_jid, waiting_time)
            self.add_behaviour(behaviour)

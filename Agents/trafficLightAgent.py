from spade.agent import Agent
from spade.template import Template
from Behaviours.trafficLightBehaviours import ReceiveCommandsBehaviour, ReceiveVehicleInfoBehaviour, ReportStatusBehaviour
import random
from spade.message import Message
import json

class TrafficLightAgent(Agent):
    """
    Agente que representa um semáforo.
    Recebe comandos do coordenador, deteta veículos (via mensagem),
    e reporta o estado/tráfego.
    """
    def __init__(self, jid, password, light_id, **kwargs):
        super().__init__(jid, password, **kwargs)
        self.light_id = light_id # ID único para o semáforo (ex: "TL_1")
        self.current_state = "RED" # Estado inicial
        self.vehicle_count = 0     # Contagem de veículos desde o último report
        self.coordinator_jid = None # Será definido no setup

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
        vehicle_info_template.set_metadata("performative", "inform")
        # Adicionar filtro por protocolo se necessário (ex: "vehicle_presence", "emergency_vehicle")
        self.add_behaviour(ReceiveVehicleInfoBehaviour(), vehicle_info_template)

        # Comportamento periódico para reportar estado/tráfego ao Coordenador
        # Reporta a cada 4 segundos (um pouco antes da lógica do coordenador)
        self.add_behaviour(ReportStatusBehaviour(period=4))

        print(f"Agente Semáforo {self.jid} ({self.light_id}) configurado. Estado inicial: {self.current_state}")

    def set_state(self, new_state, duration=None):
        """Atualiza o estado do semáforo e imprime a mudança."""
        if self.current_state != new_state:
            self.current_state = new_state
            duration_info = f"por {duration}s" if duration else ""
            print(f"--- SEMÁFORO {self.light_id} ({self.jid}): MUDOU PARA {self.current_state.upper()} {duration_info} ---")
        # Numa simulação real, aqui poder-se-ia interagir com uma GUI ou modelo físico.
        # A gestão de duração e transição (amarelo) precisaria de lógica adicional.

    def increment_vehicle_count(self):
        """Incrementa a contagem de veículos."""
        self.vehicle_count += 1
        #print(f"TL {self.light_id}: Veículo detectado. Contagem atual: {self.vehicle_count}")

    def reset_vehicle_count(self):
        """Reinicia a contagem de veículos."""
        count = self.vehicle_count
        self.vehicle_count = 0
        return count

    async def forward_emergency_alert(self, emergency_vehicle_jid):
        """Reencaminha o alerta de emergência para o coordenador."""
        print(f"TL {self.light_id}: Recebido alerta de emergência de {emergency_vehicle_jid}. Reencaminhando para Coordenador...")
        msg = Message(to=self.coordinator_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "emergency_alert")
        msg.body = json.dumps({"emergency_vehicle_jid": emergency_vehicle_jid})
        await self.send(msg)
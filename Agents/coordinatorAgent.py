from spade.agent import Agent
from spade.template import Template
from Behaviours.coordinatorBehaviours import ReceiveReportBehaviour, ControlLogicBehaviour
import time

class CoordinatorAgent(Agent):
    """
    Agente Coordenador. Gere o estado dos semáforos baseado
    no tráfego reportado e em alertas de emergência.
    """
    async def setup(self):
        print(f"Agente Coordenador {self.jid} a iniciar...")

        self.traffic_light_jids = self.get("traffic_light_jids")
        
        self.traffic_data = {}           
        self.emergency_mode = {}         
        self.traffic_light_opposites = {} 
        self.last_green_time = {jid: 0 for jid in self.traffic_light_jids}
        
        traffic_light_opposite_map = self.get("traffic_light_opposite")  

        for jid in self.traffic_light_jids:
            self.traffic_data[jid] = 0
            self.emergency_mode[jid] = False

            if traffic_light_opposite_map and jid in traffic_light_opposite_map:
                self.traffic_light_opposites[jid] = traffic_light_opposite_map[jid]
            else:
                self.traffic_light_opposites[jid] = None  

        print(f"Agente Coordenador {self.jid} configurado.")
        print(f"Semáforos conhecidos: {self.traffic_light_jids}")
        print(f"Mapeamento de semáforos opostos: {self.traffic_light_opposites}")
            

        # Comportamento para receber reports dos semáforos
        report_template = Template()
        report_template.set_metadata("performative", "inform")
        report_template.set_metadata("protocol", "traffic_report") # Protocolo para reports
        self.add_behaviour(ReceiveReportBehaviour(), report_template)

        # Comportamento para receber alertas de emergência (forwarded pelos semáforos)
        emergency_template = Template()
        emergency_template.set_metadata("performative", "inform")
        emergency_template.set_metadata("protocol", "emergency_alert") # Protocolo para alertas
        self.add_behaviour(ReceiveReportBehaviour(), emergency_template) # Reutiliza o behaviour, a lógica está lá dentro

        # Comportamento periódico para tomar decisões de controlo
        # Executa a lógica a cada 5 segundos (ajustável)
        self.add_behaviour(ControlLogicBehaviour(period=7))

        print(f"Agente Coordenador {self.jid} configurado.")
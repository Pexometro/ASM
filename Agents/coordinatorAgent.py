from spade.agent import Agent
from spade.template import Template
from Behaviours.coordinatorBehaviours import ReceiveReportBehaviour, ControlLogicBehaviour

class CoordinatorAgent(Agent):
    """
    Agente Coordenador. Gere o estado dos semáforos baseado
    no tráfego reportado e em alertas de emergência.
    """
    async def setup(self):
        print(f"Agente Coordenador {self.jid} a iniciar...")
        self.traffic_data = {} # Dicionário para guardar contagens por semáforo {tl_jid: count}
        self.emergency_mode = {} # Dicionário para estado de emergência por semáforo {tl_jid: boolean}
        self.traffic_light_jids = self.get("traffic_light_jids")

        # Inicializar dados
        for jid in self.traffic_light_jids:
            self.traffic_data[jid] = 0
            self.emergency_mode[jid] = False

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
        self.add_behaviour(ControlLogicBehaviour(period=5))

        print(f"Agente Coordenador {self.jid} configurado.")
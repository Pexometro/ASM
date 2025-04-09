from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import json

class ReceiveCommandsBehaviour(CyclicBehaviour):
    """Recebe e processa comandos do Coordenador."""
    async def run(self):
        msg = await self.receive(timeout=10)
        if msg:
            protocol = msg.metadata.get("protocol")
            # Descomentar para debug detalhado de comandos
            # print(f"TL {self.agent.light_id}: Comando '{protocol}' recebido do Coordenador.")
            if protocol == "SET_STATE":
                try:
                    data = json.loads(msg.body)
                    new_state = data.get("state")
                    duration = data.get("duration") # Duração opcional
                    if new_state in ["RED", "GREEN", "YELLOW", "RED_EMERGENCY"]:
                        self.agent.set_state(new_state, duration)
                    else:
                        print(f"TL {self.agent.light_id} ERROR: Estado inválido recebido: {new_state}")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"TL {self.agent.light_id} ERROR: Erro ao processar comando SET_STATE: {e}")
            # else: # Ignora comandos desconhecidos silenciosamente por agora
               # print(f"TL {self.agent.light_id}: Comando desconhecido recebido: {protocol}")

class ReceiveVehicleInfoBehaviour(CyclicBehaviour):
    """Recebe mensagens de veículos (contagem) e emergência (alerta)."""
    async def run(self):
        msg = await self.receive(timeout=10)
        if msg:
            sender_jid = str(msg.sender)
            protocol = msg.metadata.get("protocol")

            if protocol == "vehicle_presence":
                self.agent.increment_vehicle_count()
                #print(f"TL {self.agent.light_id}: Veículo normal {sender_jid} detectado.")

            elif protocol == "emergency_alert":
                print(f"TL {self.agent.light_id}: ALERTA de veículo de emergência {sender_jid} recebido diretamente.")
                await self.agent.forward_emergency_alert(sender_jid)


class ReportStatusBehaviour(PeriodicBehaviour):
    """Envia periodicamente o número de veículos detectados ao Coordenador."""
    async def run(self):
        # Reporta a contagem atual PRIMEIRO
        current_count = self.agent.vehicle_count
        if current_count > 0:
            print(f"TL {self.agent.light_id}: Reportando {current_count} veículos ao Coordenador.")
            msg = Message(to=self.agent.coordinator_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("protocol", "traffic_report")
            msg.body = json.dumps({"count": current_count, "current_state": self.agent.current_state})
            await self.send(msg)

            # Zera a contagem DEPOIS de reportar
            self.agent.reset_vehicle_count()
        #else:
            # Se a contagem for 0, não reporta nada (opcional, pode querer reportar 0)
            # print(f"TL {self.agent.light_id}: Sem veículos para reportar.")
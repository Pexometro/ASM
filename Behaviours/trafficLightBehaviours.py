from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
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
                    
                    # FAZER FUNÇÃO DE TRANSAÇÃOD E VERMELHO - AMARELO - VERDE
                    
                    if new_state in ["RED", "GREEN", "YELLOW", "RED_EMERGENCY"]:
                        by_emergency = data.get("by_emergency", False)
                        self.agent.emergency_active = bool(by_emergency)
                        await self.agent.set_state(new_state)

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
                self.agent.vehicles_queue.append(sender_jid)
                
                if self.agent.current_state == "GREEN":
                    print(f"TL {self.agent.light_id}: Veículo {sender_jid} detectado e já está a passar.")
                    # Enviar mensagem de permissão para o veículo
                    msg = Message(to=sender_jid)
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("protocol", "go_ahead")
                    
                    waiting_time = self.agent.vehicles_queue.index(sender_jid) * 0.5
                    
                    msg.body = json.dumps({"permission": "go", "waiting_time": waiting_time})
                    await self.send(msg)
                    
                    
                #print(f"TL {self.agent.light_id}: Presença de veículo {sender_jid} detectada.")
                

            elif protocol == "emergency_alert":
                print(f"TL {self.agent.light_id}: ALERTA de veículo de emergência {sender_jid} recebido diretamente.")
                print(f"TL {self.agent.light_id}: Reencaminhando alerta de emergência para Coordenador...")

                msg = Message(to=self.agent.coordinator_jid)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("protocol", "emergency_alert")
                msg.body = json.dumps({"emergency_vehicle_jid": sender_jid})
                await self.send(msg)
                
            elif protocol == "traffic_light_state":
                response = Message(to=str(msg.sender))
                response.set_metadata("performative", "inform")
                response.set_metadata("protocol", "traffic_light_state_reply")
                
                response.body = json.dumps({"state": self.agent.current_state})
                await self.send(response)
                
            elif protocol == "vehicle_passed":
                status = json.loads(msg.body).get("status")

                if status == "passed":
                    if sender_jid in self.agent.vehicles_queue:
                        self.agent.vehicles_queue.remove(sender_jid)
                        
                        print(f"TL {self.agent.light_id}:Veículo {sender_jid} confirmou que passou. Removido da fila.")
                        
                        current_count = len(self.agent.vehicles_queue)
                        msg = Message(to=self.agent.coordinator_jid)
                        msg.set_metadata("performative", "inform")
                        msg.set_metadata("protocol", "traffic_report")
                        msg.body = json.dumps({"count": current_count, "current_state": self.agent.current_state})
                        await self.send(msg)
                    else:
                        print(f"TL {self.agent.light_id}: Veículo {sender_jid} não estava na fila.")


class ReportStatusBehaviour(PeriodicBehaviour):
    """Envia periodicamente o número de veículos detectados ao Coordenador."""
    async def run(self):
        # Reporta a contagem atual PRIMEIRO
        current_count = len(self.agent.vehicles_queue)
        
        if current_count > 0:
            print(f"TL {self.agent.light_id}: Reportando {current_count} veículos ao Coordenador.")
            
            msg = Message(to=self.agent.coordinator_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("protocol", "traffic_report")
            msg.body = json.dumps({"count": current_count, "current_state": self.agent.current_state})
            await self.send(msg)

            
            
        #else:
            # Se a contagem for 0, não reporta nada (opcional, pode querer reportar 0)
            # print(f"TL {self.agent.light_id}: Sem veículos para reportar.")

class SendGoAheadBehaviour(OneShotBehaviour):
    def __init__(self, target_jid, waiting_time):
        super().__init__()
        self.target_jid = target_jid
        self.waiting_time = waiting_time

    async def run(self):
        msg = Message(to=self.target_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("protocol", "go_ahead")
        msg.body = json.dumps({
            "permission": "go",
            "waiting_time": self.waiting_time
        })
        await self.send(msg)
        print(f"✅ Semáforo {self.agent.light_id}: Permissão enviada a {self.target_jid} (waiting {self.waiting_time}s)")
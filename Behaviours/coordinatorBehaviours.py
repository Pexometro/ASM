from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import json # Para enviar dados estruturados no corpo da mensagem
import time 

# Limiar de tráfego para considerar ajuste (exemplo)
TRAFFIC_THRESHOLD = 1
MIN_GREEN_INTERVAL = 15  

class ReceiveReportBehaviour(CyclicBehaviour):
    """
    Recebe mensagens dos semáforos (reports de tráfego ou alertas de emergência).
    """
    
    async def run(self):
        msg = await self.receive(timeout=60) # Espera por mensagens
        
        if msg:
            sender_jid = str(msg.sender)
            protocol = msg.metadata.get("protocol")

            if protocol == "traffic_report":
                try:
                    data = json.loads(msg.body)
                    count = data.get("count", 0)
                    self.agent.traffic_data[sender_jid] = count
                    #print(f"COORD: Report recebido de {sender_jid}: {count} veículos.")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"COORD ERROR: Erro ao processar report de {sender_jid}: {e}")

            elif protocol == "emergency_alert":
                try:
                    data = json.loads(msg.body)
                    emergency_vehicle_jid = data.get("emergency_vehicle_jid")
                    print(f"COORD: ALERTA DE EMERGÊNCIA recebido via {sender_jid} relativo a {emergency_vehicle_jid}.")
                    # Marca o semáforo que reportou (e potencialmente outros) como em modo de emergência
                    self.agent.emergency_mode[sender_jid] = True
                    # NOTA: A lógica de quais semáforos afetar pode ser mais complexa
                    #       (ex: todos no cruzamento, etc.)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"COORD ERROR: Erro ao processar alerta de {sender_jid}: {e}")
            else:
                print(f"COORD: Mensagem recebida de {sender_jid} com protocolo desconhecido: {protocol}")
        #else:
            #print("COORD: Sem mensagens recebidas no último minuto.")


class ControlLogicBehaviour(PeriodicBehaviour):
    """
    Executa periodicamente a lógica de controlo dos semáforos.
    Envia comandos aos TrafficLightAgents.
    """
    
    async def run(self):
        # 1. Lógica de emergência tem prioridade
        for tl_jid, is_emergency in self.agent.emergency_mode.items():
            if is_emergency:
                print(f"COORD: Emergência detectada em {tl_jid}!")

                opposite = self.agent.traffic_light_opposites.get(tl_jid)
                if opposite:
                    await self.send_command(opposite, "SET_STATE", {"state": "RED"})
                
                await self.send_command(tl_jid, "SET_STATE", {"state": "GREEN", "by_emergency": True})

                # Reset do estado de emergência
                self.agent.emergency_mode[tl_jid] = False
                return  # Prioridade total à emergência neste ciclo

        # 2. Lógica normal adaptativa (quando não há emergência)
        now = time.time()
        busiest_traffic_light = (None, 0)

        for tl_jid in self.agent.traffic_light_jids:
            current_count = self.agent.traffic_data.get(tl_jid, 0)

            # Verifica se já passou o cooldown
            time_since_green = now - self.agent.last_green_time.get(tl_jid, 0)

            if current_count > busiest_traffic_light[1]:
                busiest_traffic_light = (tl_jid, current_count)

        if busiest_traffic_light[0]:
            opposite = self.agent.traffic_light_opposites[busiest_traffic_light[0]]
            if opposite:
                await self.send_command(opposite, "SET_STATE", {"state": "RED"})

            await self.send_command(busiest_traffic_light[0], "SET_STATE", {"state": "GREEN"})
            self.agent.last_green_time[busiest_traffic_light[0]] = now

    async def send_command(self, target_jid, command_protocol, body_dict):
        """Envia uma mensagem de comando para um semáforo."""
        msg = Message(to=target_jid)
        msg.set_metadata("performative", "request") # Usar request para comandos
        msg.set_metadata("protocol", command_protocol)
        msg.body = json.dumps(body_dict)
        await self.send(msg)
        #print(f"COORD: Comando {command_protocol} enviado para {target_jid}")
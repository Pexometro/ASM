from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import json # Para enviar dados estruturados no corpo da mensagem

# Limiar de tráfego para considerar ajuste (exemplo)
TRAFFIC_THRESHOLD = 1

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
        print("\nCOORD: Executando lógica de controlo...")

        # Lógica Simplificada:
        for tl_jid in self.agent.traffic_light_jids:
            # 1. Prioridade Emergência: Se há emergência, força vermelho (exceto talvez o próprio?)
            if self.agent.emergency_mode[tl_jid]:
                print(f"COORD: Emergência detectada para {tl_jid}. Enviando comando VERMELHO.")
                await self.send_command(tl_jid, "SET_STATE", {"state": "RED_EMERGENCY"})
                # Reset do estado de emergência após comando (lógica pode precisar ser mais robusta)
                # self.agent.emergency_mode[tl_jid] = False # Onde/Como resetar? Talvez após confirmação?
                continue # Processa próximo semáforo

            # 2. Lógica Adaptativa (Exemplo muito básico):
            #    Se um semáforo tem muito tráfego e outro pouco, ajusta tempos (simulado aqui por comando direto)
            #    NOTA: Isto é uma simplificação extrema. Uma lógica real seria muito mais complexa,
            #          envolvendo ciclos, tempos de verde/amarelo/vermelho, coordenação entre semáforos, etc.
            current_count = self.agent.traffic_data.get(tl_jid, 0)
            if current_count > TRAFFIC_THRESHOLD:
                print(f"COORD: Tráfego ALTO ({current_count}) em {tl_jid}. Enviando comando VERDE_LONGO (simulado).")
                # Simulação: apenas manda mudar para verde. A duração seria gerida no semáforo ou aqui.
                await self.send_command(tl_jid, "SET_STATE", {"state": "GREEN", "duration": 30}) # Duração exemplo
            else:
                print(f"COORD: Tráfego BAIXO ({current_count}) em {tl_jid}. Enviando comando VERMELHO (simulado).")
                await self.send_command(tl_jid, "SET_STATE", {"state": "RED"})

            # Limpa a contagem após processar (ou acumula por mais tempo?)
            self.agent.traffic_data[tl_jid] = 0


    async def send_command(self, target_jid, command_protocol, body_dict):
        """Envia uma mensagem de comando para um semáforo."""
        msg = Message(to=target_jid)
        msg.set_metadata("performative", "request") # Usar request para comandos
        msg.set_metadata("protocol", command_protocol)
        msg.body = json.dumps(body_dict)
        await self.send(msg)
        #print(f"COORD: Comando {command_protocol} enviado para {target_jid}")
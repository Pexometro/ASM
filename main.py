import spade
import time
import asyncio
import random # Importar random
import uuid   # Para gerar IDs únicos para veículos
import json

from Agents.coordinatorAgent import CoordinatorAgent
from Agents.trafficLightAgent import TrafficLightAgent
from Agents.vehicleAgent import VehicleAgent
from Agents.emergencyVehicleAgent import EmergencyVehicleAgent

from dashboard import dashboard_loop


# --- Configuração (ajusta conforme necessário) ---
XMPP_SERVER = "rui-hp-envy-x360-convertible-15-ed1xxx"  # Ou o teu servidor XMPP
PASSWORD = "NOPASSWORD"      # Password (usa uma segura se necessário)

NUM_TRAFFIC_LIGHTS = 2

# NUM_VEHICLES_PER_LIGHT = 5 # Já não criamos todos no início
COORDINATOR_JID = f"coordinator@{XMPP_SERVER}"
TRAFFIC_LIGHT_JIDS = [f"semaforo_{i}@{XMPP_SERVER}" for i in range(NUM_TRAFFIC_LIGHTS)]
# -------------------------------------------------

# Lista global para manter todos os agentes ativos para shutdown
active_agents = []

async def generate_traffic(traffic_light_jids):
    """Gera continuamente novos agentes Veículo."""
    print("--- Gerador de Tráfego Iniciado ---")
    while True:
        try:
            # Espera um tempo aleatório antes de criar o próximo veículo
            # Ajusta estes valores para controlar a taxa de chegada
            await asyncio.sleep(random.uniform(1.0, 5.0))

            # Escolhe um semáforo alvo aleatoriamente
            target_semaforo_jid = random.choice(traffic_light_jids)

            # Cria um ID único para o novo veículo
            vehicle_id = str(uuid.uuid4())[:8] # ID curto
            vehicle_jid = f"vehicle_{vehicle_id}@{XMPP_SERVER}"

            print(f"--- Gerando novo veículo {vehicle_jid} para {target_semaforo_jid} ---")
            vehicle = VehicleAgent(vehicle_jid, PASSWORD)
            vehicle.set("target_traffic_light_jid", target_semaforo_jid)

            await vehicle.start(auto_register=True)
            active_agents.append(vehicle) # Adiciona à lista para poder parar depois

        except Exception as e:
            print(f"Erro no gerador de tráfego: {e}")
            await asyncio.sleep(5) # Espera antes de tentar novamente


async def main():
    global active_agents # Para poder adicionar agentes a partir daqui e de generate_traffic
    print("Iniciando configuração dos agentes...")
    
    with open("cenario_1.json", "r") as f:
        cenario = json.load(f)

    semaforos_config = cenario["semaforos"]
    
    traffic_lights = []
    TRAFFIC_LIGHT_JIDS = []

    for semaforo_id, info in semaforos_config.items():
        jid = f"{semaforo_id}@{XMPP_SERVER}"
        TRAFFIC_LIGHT_JIDS.append(jid)
        
        
    # --- Criar Agentes Semáforo ---
    for semaforo_id, info in semaforos_config.items():
        jid = f"{semaforo_id}@{XMPP_SERVER}"
        traffic_light = TrafficLightAgent(jid, PASSWORD, light_id=semaforo_id, passadeira=info["passadeira"], oposto=info["oposto"])
        traffic_light.set("coordinator_jid", COORDINATOR_JID)
        traffic_light.set("passadeira", info["passadeira"])
        traffic_light.set("oposto", info["oposto"])  # Guarda info do semáforo oposto, se for relevante para lógica futura

        await traffic_light.start(auto_register=True)
        active_agents.append(traffic_light)
        traffic_lights.append(traffic_light)
        print(f"Agente Semáforo iniciado: {traffic_light.jid}")
        await asyncio.sleep(0.5)
        
    dashboard_task = asyncio.create_task(dashboard_loop(traffic_lights))
    
    # --- Criar o dicionário dos opostos ---    
    traffic_light_opposites = {}
    for semaforo_id, info in semaforos_config.items():
        jid = f"{semaforo_id}@{XMPP_SERVER}"
        oposto_id = info.get("oposto")

        if oposto_id:
            oposto_jid = f"{oposto_id}@{XMPP_SERVER}"
            traffic_light_opposites[jid] = oposto_jid
        else:
            traffic_light_opposites[jid] = None

    # --- Criar Agente Coordenador ---
    coordinator = CoordinatorAgent(f"{COORDINATOR_JID}", PASSWORD)
    coordinator.set("traffic_light_jids", TRAFFIC_LIGHT_JIDS)
    coordinator.set("traffic_light_opposite", traffic_light_opposites)
    await coordinator.start(auto_register=True)
    active_agents.append(coordinator)
    print(f"Agente Coordenador iniciado: {coordinator.jid}")
    await asyncio.sleep(1)

    

    # --- Iniciar Gerador de Tráfego (em background) ---
    # Cria uma task que corre a função generate_traffic independentemente
    traffic_task = asyncio.create_task(generate_traffic(TRAFFIC_LIGHT_JIDS))

    # --- Criar Agente Veículo de Emergência (Dummy) ---
    # Exemplo: criar uma ambulância após 20 segundos (dá tempo para algum tráfego se acumular)
    await asyncio.sleep(20)
    print("\n--- A criar Veículo de Emergência ---")
    emergency_jid = f"ambulance_1@{XMPP_SERVER}"
    target_semaforo_for_emergency = random.choice(TRAFFIC_LIGHT_JIDS) # Escolhe um semáforo aleatório para a emergência
    
    # ---------------------------------------------------------------------------------------------------------
    
    #emergency_vehicle = EmergencyVehicleAgent(emergency_jid, PASSWORD)
    #emergency_vehicle.set("target_traffic_light_jid", target_semaforo_for_emergency)
    #await emergency_vehicle.start(auto_register=True)
    #active_agents.append(emergency_vehicle)
    #print(f"Agente Veículo de Emergência iniciado: {emergency_vehicle.jid} -> {target_semaforo_for_emergency}")

    # ---------------------------------------------------------------------------------------------------------
    

    print("\n--- Simulação a correr ---")
    print("Pressiona CTRL+C para parar.")

    try:
        # Mantem a execução principal ativa (a geração de tráfego corre em background)
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupção recebida, a parar simulação...")
        # Cancela a tarefa de geração de tráfego
        traffic_task.cancel()
        try:
            await traffic_task # Espera que a tarefa seja cancelada
        except asyncio.CancelledError:
            print("Gerador de tráfego parado.")

        print("A parar agentes...")
        # Faz uma cópia da lista para iterar, caso haja modificações durante o stop
        agents_to_stop = list(active_agents)
        for agent in agents_to_stop:
            try:
                if agent.is_alive():
                    await agent.stop()
                    #print(f"Agente {agent.jid} parado.")
            except Exception as e:
                print(f"Erro ao parar agente {agent.jid}: {e}")
        print("Todos os agentes que podiam ser parados foram processados.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulação terminada pelo utilizador.")
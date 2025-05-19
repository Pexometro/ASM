from rich.live import Live
from rich.table import Table
import asyncio

async def dashboard_loop(traffic_lights):
    """Mostra o estado dos semáforos em tempo real no terminal."""
    with Live(refresh_per_second=1) as live:
        while True:
            table = Table(title="Estado dos Semáforos", show_lines=True)
            table.add_column("ID", style="bold cyan")
            table.add_column("Estado", justify="center")
            table.add_column("Carros em Espera", justify="center")
            table.add_column("Emergência Ativa", justify="center")

            for tl in traffic_lights:
                estado = tl.current_state.upper()
                carros = str(len(tl.vehicles_queue))

                # Indicação visual do estado
                if estado == "RED":
                    estado_visual = "[red]🔴 VERMELHO[/red]"
                elif estado == "YELLOW":
                    estado_visual = "[yellow]🟡 AMARELO[/yellow]"
                elif estado == "GREEN":
                    # Diferenciar se está verde por emergência
                    emergencia = getattr(tl, "emergency_active", False)
                    if emergencia:
                        estado_visual = "[bold green]🟢 VERDE (EMERGÊNCIA)[/bold green]"
                    else:
                        estado_visual = "[green]🟢 VERDE[/green]"
                elif estado == "RED_EMERGENCY":
                    estado_visual = "[bold red]🚨 VERMELHO EMERGÊNCIA[/bold red]"
                else:
                    estado_visual = f"[white]{estado}[/white]"

                # Emergência ativa?
                emergencia_ativa = "🚑" if getattr(tl, "emergency_active", False) else "➖"

                table.add_row(
                    tl.light_id,
                    estado_visual,
                    carros,
                    emergencia_ativa
                )

            live.update(table)
            await asyncio.sleep(1)

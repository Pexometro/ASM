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
            table.add_column("Emergência", justify="center")

            for tl in traffic_lights:
                estado = tl.current_state.upper()
                carros = str(tl.vehicle_count)
                emergencia = "🚨" if estado == "RED_EMERGENCY" else "➖"

                # Tratamento do estado visual
                if estado == "RED":
                    estado_visual = "[red]🔴 VERMELHO[/red]"
                elif estado == "YELLOW":
                    estado_visual = "[yellow]🟡 AMARELO[/yellow]"
                elif estado == "GREEN":
                    estado_visual = "[green]🟢 VERDE[/green]"
                elif estado == "RED_EMERGENCY":
                    estado_visual = "[bold red]🚨 VERMELHO EMERGÊNCIA[/bold red]"
                else:
                    estado_visual = f"[white]{estado}[/white]"

                table.add_row(
                    tl.light_id,
                    estado_visual,
                    carros,
                    emergencia
                )

            live.update(table)
            await asyncio.sleep(1)

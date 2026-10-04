"""Main entry point for Facebook Automation Suite."""

import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.browser import BrowserEngine
from src.core.scheduler import PostScheduler
from src.modules.poster import FacebookPoster
from src.utils.helpers import load_yaml_config
from src.utils.logger import logger

console = Console()

BANNER = """
[bold cyan]███████╗██████╗      █████╗ ██╗   ██╗████████╗ ██████╗ [/bold cyan]
[bold cyan]██╔════╝██╔══██╗    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗[/bold cyan]
[bold cyan]█████╗  ██████╔╝    ███████║██║   ██║   ██║   ██║   ██║[/bold cyan]
[bold cyan]██╔══╝  ██╔══██╗    ██╔══██║██║   ██║   ██║   ██║   ██║[/bold cyan]
[bold cyan]██║     ██████╔╝    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝[/bold cyan]
[bold cyan]╚═╝     ╚═════╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ [/bold cyan]
[bold green]    ⚡ High-Performance Stealth Facebook Automation ⚡    [/bold green]
"""

def print_welcome_banner():
    """Renders the aesthetic terminal banner for clients and users."""
    console.print(BANNER)
    panel = Panel(
        "[white]Production-Ready Facebook Post Automation Engine[/white]\n"
        "[dim]Stealth Execution • Session Persistence • Smart Post Scheduler[/dim]\n"
        "[yellow]Author: Mahmud Hasan | Open-Source Edition[/yellow]",
        title="[bold blue]Facebook-Automation-Suite[/bold blue]",
        border_style="cyan",
    )
    console.print(panel)
    console.print()

async def run_single_post(content: str, media_paths: list = None, target_url: str = "https://www.facebook.com/"):
    """Executes a single post publishing job."""
    engine = BrowserEngine()
    try:
        poster = FacebookPoster(engine)
        success = await poster.create_post(
            content=content,
            media_paths=media_paths,
            target_url=target_url,
        )
        return success
    finally:
        await engine.close()

async def run_campaign_scheduler(config_path: Path):
    """Executes the campaign scheduler based on YAML configuration."""
    config = load_yaml_config(config_path)
    campaigns = config.get("campaigns", [])

    if not campaigns:
        console.print("[yellow]⚠️ No campaigns found in settings. Please check your config file.[/yellow]")
        return

    table = Table(title="Scheduled Campaigns", border_style="cyan")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Target", style="green")
    table.add_column("Time", style="yellow")

    scheduler = PostScheduler()

    for c in campaigns:
        table.add_row(c.get("id"), c.get("title"), c.get("target"), c.get("schedule_time"))
        
        # Schedule each post
        def make_job(camp):
            def job():
                asyncio.run(run_single_post(
                    content=camp.get("content", ""),
                    media_paths=camp.get("images", []),
                ))
            return job

        scheduler.add_daily_job(c.get("schedule_time", "09:00"), make_job(c))

    console.print(table)
    console.print("[green]Scheduler running. Press Ctrl+C to stop.[/green]")
    await scheduler.start()

async def interactive_cli():
    """Interactive CLI menu when run without command line flags."""
    print_welcome_banner()

    while True:
        console.print("[bold]Select an action:[/bold]")
        console.print("[1] 🚀 Publish a Quick Post Now")
        console.print("[2] ⏰ Run Scheduled Campaigns (settings.yaml)")
        console.print("[3] 🔑 Test & Save Facebook Login Session")
        console.print("[0] 🚪 Exit")

        choice = input("\nEnter choice [0-3]: ").strip()

        if choice == "1":
            post_text = input("\nEnter post caption/text: ").strip()
            if post_text:
                console.print("\n[cyan]Starting automated post sequence...[/cyan]")
                await run_single_post(content=post_text)
            else:
                console.print("[red]Post text cannot be empty.[/red]")

        elif choice == "2":
            config_file = Path(__file__).resolve().parent.parent / "config" / "settings.example.yaml"
            await run_campaign_scheduler(config_file)

        elif choice == "3":
            console.print("\n[cyan]Testing Facebook authentication...[/cyan]")
            engine = BrowserEngine(headless=False)
            try:
                _, page = await engine.initialize()
                poster = FacebookPoster(engine)
                await poster.verify_login_state(page)
                await engine.save_session()
                console.print("[green]Session verification complete.[/green]")
            finally:
                await engine.close()

        elif choice == "0":
            console.print("[bold cyan]Goodbye![/bold cyan]")
            break
        else:
            console.print("[red]Invalid choice. Please select 0, 1, 2, or 3.[/red]\n")

def main():
    parser = argparse.ArgumentParser(description="Facebook Automation Suite CLI")
    parser.add_argument("--post", type=str, help="Publish a single post immediately with given content")
    parser.add_argument("--media", nargs="*", help="Paths to media/images to attach with the post")
    parser.add_argument("--schedule", action="store_true", help="Start the background campaign scheduler")
    parser.add_argument("--config", type=str, default="config/settings.example.yaml", help="Path to YAML settings file")

    args = parser.parse_args()

    if args.post:
        asyncio.run(run_single_post(content=args.post, media_paths=args.media))
    elif args.schedule:
        asyncio.run(run_campaign_scheduler(Path(args.config)))
    else:
        asyncio.run(interactive_cli())

if __name__ == "__main__":
    main()

import typer
import httpx
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False)
media_app = typer.Typer(help="Media management commands")
system_app = typer.Typer(help="System management commands")

# Add the command groups to the main app
app.add_typer(media_app, name="media")
app.add_typer(system_app, name="system")

console = Console()

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

async def make_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make an HTTP request to the API"""
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
        url = f"{API_BASE_URL}/{endpoint}"
        try:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(1)

# Media commands
@media_app.command()
def refresh():
    """Refresh the media library"""
    console.print("[yellow]Refreshing media library...[/yellow]")
    result = asyncio.run(make_request("POST", "api/media/refresh"))
    console.print(f"[green]Success:[/green] {result['message']}")

@media_app.command()
def merge(refresh: bool = typer.Option(False, "--refresh", "-r", help="Refresh the media library after merging")):
    """Merge the media library"""
    console.print("[yellow]Merging media library...[/yellow]")
    result = asyncio.run(make_request("POST", f"api/media/merge?refresh={str(refresh).lower()}"))
    console.print(f"[green]Success:[/green] {result['message']}")
    if refresh and result.get('data', {}).get('refresh'):
        console.print(f"[green]Refresh Status:[/green] {result['data']['refresh']}")

@media_app.command()
def hot_cache():
    """Get the hot cache status"""
    console.print("[yellow]Getting hot cache status...[/yellow]")
    result = asyncio.run(make_request("GET", "api/media/cache/hot"))
    console.print(f"[green]Success:[/green] {result['message']}")

# System commands
@system_app.command()
def health():
    """Check system health"""
    console.print("[yellow]Checking system health...[/yellow]")
    result = asyncio.run(make_request("GET", "system/health"))
    console.print(f"[green]Status:[/green] {result['status']}")
    console.print(f"[green]Timestamp:[/green] {result['timestamp']}")

if __name__ == "__main__":
    app() 
import typer
import httpx
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(add_completion=False)
media_app = typer.Typer(help="Media management commands")
system_app = typer.Typer(help="System management commands")
cache_app = typer.Typer(help="Cache management commands")

# Add the command groups to the main app
app.add_typer(media_app, name="media")
app.add_typer(system_app, name="system")
app.add_typer(cache_app, name="cache")

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
def merge(
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Refresh the media library after merging"),
    details: bool = typer.Option(False, "--details", "-d", help="Show detailed changes for each media type")
):
    """Merge the media library"""
    console.print("[yellow]Merging media library...[/yellow]")
    result = asyncio.run(make_request("POST", f"api/media/merge?refresh={str(refresh).lower()}"))
    console.print(f"[green]Success:[/green] {result['message']}")
    
    # Display changes in a table only if details option is specified
    if details and result.get('data', {}).get('merge'):
        for media_type, merge_result in result['data']['merge'].items():
            table = Table(title=f"{media_type.title()} Changes")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="green")
            
            # Count added folders
            added_count = len(merge_result.get('added_folders', {}))
            table.add_row("Added", str(added_count))
            
            # Count updated folders
            updated_count = len(merge_result.get('updated_folders', {}))
            table.add_row("Updated", str(updated_count))
            
            # Count deleted folders
            deleted_count = len(merge_result.get('deleted_folders', []))
            table.add_row("Removed", str(deleted_count))
            
            console.print(table)
    
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

# Cache commands
@cache_app.command()
def list(
    cache_type: str = typer.Option("all", "--type", "-t", help="Cache type to list [hot|cold|all]")
):
    """List cache contents"""
    if cache_type not in ["hot", "cold", "all"]:
        console.print("[red]Error:[/red] Cache type must be one of: hot, cold, all")
        raise typer.Exit(1)
        
    console.print(f"[yellow]Listing {cache_type} cache contents...[/yellow]")
    result = asyncio.run(make_request("GET", f"api/cache/{cache_type}"))
    console.print(f"[green]Success:[/green] {result['message']}")

@cache_app.command()
def list_all():
    """List all cache contents"""
    console.print("[yellow]Listing all cache contents...[/yellow]")
    result = asyncio.run(make_request("GET", "api/cache/list"))
    console.print(f"[green]Success:[/green] {result['message']}")

if __name__ == "__main__":
    app() 
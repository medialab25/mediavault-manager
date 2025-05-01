import typer
import httpx
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table
from app.core.config import Config
from app.api.managers.media_manager import MediaManager
from app.core.status import Status

app = typer.Typer()
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
            result = response.json()
            
            # Handle APIResponse format
            if isinstance(result, dict) and "status" in result and "message" in result:
                if result["status"] == Status.ERROR:
                    console.print(f"[red]Error:[/red] {result['message']}")
                    raise typer.Exit(1)
                return result
            return result
        except httpx.HTTPError as e:
            error_detail = e.response.json() if e.response and e.response.content else {"message": str(e)}
            if isinstance(error_detail, dict) and "detail" in error_detail:
                if isinstance(error_detail["detail"], dict):
                    console.print(f"[red]Error:[/red] {error_detail['detail'].get('message', str(e))}")
                else:
                    console.print(f"[red]Error:[/red] {error_detail['detail']}")
            else:
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

# Search command
@app.command()
def search(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query string"),
    media_type: Optional[str] = typer.Option(None, "--media-type", "-m", help="Media type (tv,movie)"),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="Quality (hd,uhd,4k)"),
    id: Optional[str] = typer.Option(None, "--id", "-i", help="Media ID to search for")
):
    """Search for media using the search request endpoint"""
    try:
        # If no query or id provided, show help and exit
        if not query and not id:
            console.print("[yellow]No search query or ID provided.[/yellow]")
            console.print(ctx.get_help())
            return

        search_term = id if id else query
        console.print(f"[yellow]Searching for '{search_term}'...[/yellow]")
        
        # Build query parameters
        params = {}
        if query:
            params["query"] = query
        if id:
            params["id"] = id
        if media_type is not None:
            params["media_type"] = media_type
        if quality is not None:
            params["quality"] = quality
            
        # Convert params to query string
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        result = asyncio.run(make_request("GET", f"api/search/?{query_string}"))
        
        console.print(f"[green]Success:[/green] {result['message']}")
        
        # Display the data if it exists
        if result.get('data'):
            console.print("\n[cyan]Search Results:[/cyan]")
            console.print_json(data=result['data'])
        else:
            console.print("[yellow]No results found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

# System commands
@system_app.command()
def health():
    """Check system health"""
    console.print("[yellow]Checking system health...[/yellow]")
    result = asyncio.run(make_request("GET", "system/health"))
    console.print(f"[green]Status:[/green] {result['message']}")
    if result.get('data', {}).get('timestamp'):
        console.print(f"[green]Timestamp:[/green] {result['data']['timestamp']}")

# Cache commands
@cache_app.command()
def list():
    """List all cache contents"""
    try:
        console.print("[yellow]Listing all cache contents...[/yellow]")
        result = asyncio.run(make_request("GET", "api/cache/list"))
        console.print(f"[green]Success:[/green] {result['message']}")
        
        # Display the data if it exists
        if result.get('data'):
            console.print("\n[cyan]Cache Data:[/cyan]")
            console.print_json(data=result['data'])
        else:
            console.print("[yellow]No data returned[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@cache_app.command()
def find(
    title: str = typer.Argument(..., help="Title to search for"),
    season: Optional[int] = typer.Option(None, "--season", "-s", help="Season number"),
    episode: Optional[int] = typer.Option(None, "--episode", "-e", help="Episode number"),
    media_prefix: Optional[str] = typer.Option(None, "--media-prefix", "-p", help="Media prefix"),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="Quality"),
    media_type: Optional[str] = typer.Option(None, "--media-type", "-t", help="Media type (tv,movie)"),
    search_cache: bool = typer.Option(False, "--search-cache", "-c", help="Search in cache")
):
    """Find media in cache by title and optional parameters"""
    try:
        console.print(f"[yellow]Searching for '{title}'...[/yellow]")
        
        # Build query parameters
        params = {"title": title}
        if season is not None:
            params["season"] = season
        if episode is not None:
            params["episode"] = episode
        if media_prefix is not None:
            params["media_prefix"] = media_prefix
        if quality is not None:
            params["quality"] = quality
        if media_type is not None:
            params["media_type"] = media_type
        if search_cache:
            params["search_cache"] = "true"
            
        # Convert params to query string
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        result = asyncio.run(make_request("GET", f"api/cache/find?{query_string}"))
        
        console.print(f"[green]Success:[/green] {result['message']}")
        
        # Display the data if it exists
        if result.get('data'):
            console.print("\n[cyan]Search Results:[/cyan]")
            console.print_json(data=result['data'])
        else:
            console.print("[yellow]No results found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 
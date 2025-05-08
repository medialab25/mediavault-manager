import typer
import httpx
import asyncio
from typing import Optional
from rich.console import Console
from rich.table import Table
from app.api.models.media_models import MediaDbType
from app.api.models.search_request import SearchCacheExportFilter
from app.core.config import Config
from app.api.managers.media_manager import MediaManager
from app.core.status import Status
from app.cli.settings import cli_settings
import json

app = typer.Typer()
media_app = typer.Typer(help="Media management commands")
system_app = typer.Typer(help="System management commands")
cache_app = typer.Typer(help="Cache management commands")

# Add the command groups to the main app
app.add_typer(media_app, name="media")
app.add_typer(system_app, name="system")
app.add_typer(cache_app, name="cache")

console = Console()

async def make_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make an HTTP request to the API"""
    async with httpx.AsyncClient(timeout=cli_settings.TIMEOUT) as client:
        url = f"{cli_settings.API_BASE_URL}/{endpoint}"
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
            try:
                error_detail = e.response.json() if e.response and e.response.content else {"message": str(e)}
                if isinstance(error_detail, dict):
                    if "detail" in error_detail:
                        if isinstance(error_detail["detail"], dict):
                            # Handle APIResponse error format
                            if "message" in error_detail["detail"]:
                                console.print(f"[red]Error:[/red] {error_detail['detail']['message']}")
                            else:
                                console.print(f"[red]Error:[/red] {error_detail['detail']}")
                        else:
                            console.print(f"[red]Error:[/red] {error_detail['detail']}")
                    else:
                        console.print(f"[red]Error:[/red] {str(e)}")
                else:
                    console.print(f"[red]Error:[/red] {str(e)}")
            except json.JSONDecodeError:
                # Handle non-JSON error responses
                error_message = e.response.text if e.response and e.response.text else str(e)
                console.print(f"[red]Error:[/red] {error_message}")
            raise typer.Exit(1)

# Media commands
@media_app.command()
def refresh():
    """Refresh the media library"""
    console.print("[yellow]Refreshing media library...[/yellow]")
    result = asyncio.run(make_request("POST", "api/media/refresh"))
    console.print(f"[green]Success:[/green] {result['message']}")

@media_app.command()
def update():
    """Update the media library by scanning for changes and updating metadata"""
    console.print("[yellow]Updating media library...[/yellow]")
    result = asyncio.run(make_request("POST", "api/media/update"))
    console.print(f"[green]Success:[/green] {result['message']}")

# Search command
@app.command()
def search(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query string"),
    media_type: Optional[str] = typer.Option(None, "--media-type", "-m", help="Media type (tv,movie)"),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="Quality (hd,uhd,4k)"),
    add_extended_info: bool = typer.Option(False, "--extended-info", "-e", help="Add extended info"),
    season: Optional[int] = typer.Option(None, "--season", "-s", help="Season number"),
    episode: Optional[int] = typer.Option(None, "--episode", "-e", help="Episode number"),
    db_type: Optional[str] = typer.Option("media", "--db-type", "-d", help="Database types (comma-separated: media,cache,shadow)"),
    matrix_filepath: Optional[str] = typer.Option(None, "--matrix-filepath", "-f", help="Matrix filepath"),
    relative_filepath: Optional[str] = typer.Option(None, "--relative-filepath", "-r", help="Relative filepath"),
    cache_export_filter: Optional[str] = typer.Option(None, "--cache-export-filter", "-c", help="Cache export filter (comma-separated: all,cache_export,not_cache_export)")
):
    """Search for media using the search request endpoint"""
    try:
        # If no query or id provided, show help and exit
        if not query:
            console.print("[yellow]No search query provided.[/yellow]")
            console.print(ctx.get_help())
            return

        search_term = query
        console.print(f"[yellow]Searching for '{search_term}'...[/yellow]")
        
        # Build query parameters
        params = {}
        if query:
            params["query"] = query
        if matrix_filepath is not None:
            params["matrix_filepath"] = matrix_filepath
        if relative_filepath is not None:
            params["relative_filepath"] = relative_filepath
        if media_type is not None:
            params["media_type"] = media_type
        if quality is not None:
            params["quality"] = quality
        if season is not None:
            params["season"] = season
        if episode is not None:
            params["episode"] = episode
        if add_extended_info:
            params["add_extended_info"] = add_extended_info
        if db_type is not None:
            # Validate each db_type
            for t in db_type.split(","):
                try:
                    MediaDbType(t.strip())
                except ValueError:
                    console.print(f"[red]Error:[/red] Invalid database type '{t}'. Valid types are: {', '.join(t.value for t in MediaDbType)}")
                    raise typer.Exit(1)
            params["db_type"] = db_type
        if cache_export_filter is not None:
            try:
                params["cache_export_filter"] = SearchCacheExportFilter(cache_export_filter).value
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid cache export filter '{cache_export_filter}'. Valid types are: {', '.join(t.value for t in SearchCacheExportFilter)}")
                raise typer.Exit(1)
            
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
    result = asyncio.run(make_request("GET", "api/system/health"))
    console.print(f"[green]Status:[/green] {result['message']}")
    if result.get('data', {}).get('timestamp'):
        console.print(f"[green]Timestamp:[/green] {result['data']['timestamp']}")
    if result.get('data', {}).get('media_library_update_request_count'):
        console.print(f"[green]Media library update request count:[/green] {result['data']['media_library_update_request_count']}")

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
def add(
    query: Optional[str] = typer.Argument(None, help="Search query string"),
    media_type: Optional[str] = typer.Option(None, "--media-type", "-m", help="Media type (tv,movie)"),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="Quality (hd,uhd,4k)"),
    season: Optional[int] = typer.Option(None, "--season", "-s", help="Season number"),
    episode: Optional[int] = typer.Option(None, "--episode", "-e", help="Episode number"),
    matrix_filepath: Optional[str] = typer.Option(None, "--matrix-filepath", "-f", help="Matrix filepath"),
    relative_filepath: Optional[str] = typer.Option(None, "--relative-filepath", "-r", help="Relative filepath"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be added without making changes"),
):
    """Add an item to the cache"""
    try:
        if dry_run:
            console.print("[yellow]Dry run - showing what would be added to cache...[/yellow]")
        else:
            console.print(f"[yellow]Adding item(s) to cache...[/yellow]")
        
        result = asyncio.run(make_request("POST", "api/cache/add", data={
            "query": query, 
            "media_type": media_type, 
            "quality": quality, 
            "season": season, 
            "episode": episode,
            "matrix_filepath": matrix_filepath,
            "relative_filepath": relative_filepath,
            "dry_run": dry_run
        }))
        
        if dry_run:
            console.print(f"[green]Dry run completed:[/green] {result['message']}")
        else:
            console.print(f"[green]Success:[/green] {result['message']}")
        
        # Display the data if it exists
        if result.get('data'):
            if dry_run:
                console.print("\n[cyan]Files that would be added to cache:[/cyan]")
            else:
                console.print("\n[cyan]Files added to cache:[/cyan]")
            console.print_json(data=result['data'])
        else:
            console.print("[yellow]No results found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
    
@cache_app.command()
def remove(
    query: Optional[str] = typer.Argument(None, help="Search query string"),
    media_type: Optional[str] = typer.Option(None, "--media-type", "-m", help="Media type (tv,movie)"),
    quality: Optional[str] = typer.Option(None, "--quality", "-q", help="Quality (hd,uhd,4k)"),
    id: Optional[str] = typer.Option(None, "--id", "-i", help="Media ID to search for"),
    season: Optional[int] = typer.Option(None, "--season", "-s", help="Season number"),
    episode: Optional[int] = typer.Option(None, "--episode", "-e", help="Episode number"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be removed without making changes"),
):
    """Remove an item from the cache"""
    try:
        if dry_run:
            console.print("[yellow]Dry run - showing what would be removed from cache...[/yellow]")
        else:
            console.print(f"[yellow]Removing item(s) from cache...[/yellow]")
        
        result = asyncio.run(make_request("POST", "api/cache/remove", data={
            "query": query, 
            "media_type": media_type, 
            "quality": quality, 
            "id": id, 
            "season": season, 
            "episode": episode,
            "dry_run": dry_run
        }))
        
        if dry_run:
            console.print(f"[green]Dry run completed:[/green] {result['message']}")
        else:
            console.print(f"[green]Success:[/green] {result['message']}")
        
        # Display the data if it exists
        if result.get('data'):
            if dry_run:
                console.print("\n[cyan]Files that would be removed from cache:[/cyan]")
            else:
                console.print("\n[cyan]Files removed from cache:[/cyan]")
            console.print_json(data=result['data'])
        else:
            console.print("[yellow]No results found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@cache_app.command()
def clear_pre_cache():
    """Clear the pre cache"""
    try:
        console.print("[yellow]Clearing pre cache...[/yellow]")
        result = asyncio.run(make_request("POST", "api/cache/pre-cache/clear"))
        console.print(f"[green]Success:[/green] {result['message']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def sync(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be synced without making changes"),
    details: bool = typer.Option(False, "--details", "-d", help="Show details of the sync operation"),
    force: bool = typer.Option(False, "--force", "-f", help="Force sync even if the media library update request count is 0"),
):
    """Sync the cache with the media library"""
    if dry_run:
        console.print("[yellow]Dry run - showing what would be synced...[/yellow]")
    else:
        console.print("[yellow]Syncing cache with media library...[/yellow]")
    
    result = asyncio.run(make_request("POST", "api/sync/", data={"dry_run": dry_run, "details": details, "force": force}))
    
    # Display the data if it exists
    if result.get('data'):
        if dry_run:
            console.print("\n[cyan]Files that would be synced:[/cyan]")
        else:
            console.print("\n[cyan]Files synced:[/cyan]")
        console.print_json(data=result['data'])
    else:
        console.print("[yellow]No results found[/yellow]") 
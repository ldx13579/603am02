from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from app.services.report import generate_report
from app.services.git_analyzer import analyze_repo, CommitInfo
from app.services.smart_analysis import run_smart_analysis

app = typer.Typer(name="git-habits", help="Cross-repository Git commit habit analysis CLI")
console = Console()


def load_repos_config(config_path: str) -> list[dict]:
    path = Path(config_path)
    if not path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    repos = data.get("repos", [])
    if not repos:
        console.print("[yellow]No repositories configured in YAML[/yellow]")
        raise typer.Exit(1)

    return repos


@app.command()
def analyze(
    config: str = typer.Option("repos.yaml", "--config", "-c", help="Path to repos YAML config"),
    output: str = typer.Option(None, "--output", "-o", help="Output JSON file path"),
    since: str = typer.Option(None, "--since", help="Start date (YYYY-MM-DD)"),
    until: str = typer.Option(None, "--until", help="End date (YYYY-MM-DD)"),
    repo_name: str = typer.Option(None, "--repo", "-r", help="Analyze specific repo by name"),
):
    """Analyze Git commit habits across configured repositories."""
    repos = load_repos_config(config)

    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None
    until_dt = datetime.strptime(until, "%Y-%m-%d") if until else None

    if repo_name:
        repos = [r for r in repos if r["name"] == repo_name]
        if not repos:
            console.print(f"[red]Repository '{repo_name}' not found in config[/red]")
            raise typer.Exit(1)

    reports = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        for repo_conf in repos:
            task = progress.add_task(f"Scanning {repo_conf['name']}...", total=None)

            def on_progress(current: int, total: int):
                progress.update(task, total=total, completed=current)

            try:
                report = generate_report(
                    repo_name=repo_conf["name"],
                    repo_path=repo_conf["path"],
                    branch=repo_conf.get("branch", "main"),
                    since=since_dt,
                    until=until_dt,
                    progress_callback=on_progress,
                )
                reports.append(report)
                progress.update(task, description=f"[green]Done: {repo_conf['name']}[/green]")
            except FileNotFoundError as e:
                progress.update(task, description=f"[red]Not found: {repo_conf['name']}[/red]")
                console.print(f"  [red]{e}[/red]")
            except PermissionError as e:
                progress.update(task, description=f"[red]Permission denied: {repo_conf['name']}[/red]")
                console.print(f"  [red]{e}[/red]")
            except Exception as e:
                progress.update(task, description=f"[red]Error: {repo_conf['name']}[/red]")
                console.print(f"  [red]{type(e).__name__}: {e}[/red]")

    if not reports:
        console.print("[yellow]No reports generated.[/yellow]")
        raise typer.Exit(1)

    result = {"generated_at": datetime.now().isoformat(), "reports": reports}

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]Report saved to: {output}[/green]")
    else:
        _print_summary(reports)


@app.command()
def list_repos(
    config: str = typer.Option("repos.yaml", "--config", "-c", help="Path to repos YAML config"),
):
    """List configured repositories."""
    repos = load_repos_config(config)

    table = Table(title="Configured Repositories")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Branch", style="green")

    for repo in repos:
        table.add_row(repo["name"], repo["path"], repo.get("branch", "main"))

    console.print(table)


@app.command()
def export_json(
    config: str = typer.Option("repos.yaml", "--config", "-c"),
    output: str = typer.Option("report.json", "--output", "-o"),
    since: str = typer.Option(None, "--since"),
    until: str = typer.Option(None, "--until"),
):
    """Export full analysis as JSON report."""
    analyze(config=config, output=output, since=since, until=until, repo_name=None)


@app.command()
def smart_analyze(
    config: str = typer.Option("repos.yaml", "--config", "-c", help="Path to repos YAML config"),
    since: str = typer.Option(None, "--since", help="Start date (YYYY-MM-DD)"),
    until: str = typer.Option(None, "--until", help="End date (YYYY-MM-DD)"),
    repo_name: str = typer.Option(None, "--repo", "-r", help="Analyze specific repo by name"),
    output_dir: str = typer.Option("./output", "--output-dir", "-d", help="Directory for output images"),
):
    """Smart analysis: TF-IDF keywords, word cloud, late-night ratio, and schedule heatmap."""
    repos = load_repos_config(config)

    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None
    until_dt = datetime.strptime(until, "%Y-%m-%d") if until else None

    if repo_name:
        repos = [r for r in repos if r["name"] == repo_name]
        if not repos:
            console.print(f"[red]Repository '{repo_name}' not found in config[/red]")
            raise typer.Exit(1)

    all_commits: list[CommitInfo] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        for repo_conf in repos:
            task = progress.add_task(f"Scanning {repo_conf['name']}...", total=None)

            def on_progress(current: int, total: int):
                progress.update(task, total=total, completed=current)

            try:
                commits = analyze_repo(
                    repo_path=repo_conf["path"],
                    branch=repo_conf.get("branch", "main"),
                    since=since_dt,
                    until=until_dt,
                    progress_callback=on_progress,
                )
                all_commits.extend(commits)
                progress.update(task, description=f"[green]Done: {repo_conf['name']} ({len(commits)} commits)[/green]")
            except Exception as e:
                progress.update(task, description=f"[red]Error: {repo_conf['name']}[/red]")
                console.print(f"  [red]{type(e).__name__}: {e}[/red]")

    if not all_commits:
        console.print("[yellow]No commits found across repositories.[/yellow]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Merged {len(all_commits)} commits from {len(repos)} repo(s)[/bold]")
    console.print("[dim]Running smart analysis...[/dim]\n")

    out_path = Path(output_dir)
    result = run_smart_analysis(all_commits, out_path)

    table = Table(title="Top Keywords (TF-IDF)")
    table.add_column("Keyword", style="cyan")
    table.add_column("Score", justify="right", style="green")
    for word, score in result["keywords"][:15]:
        table.add_row(word, f"{score:.3f}")
    console.print(table)

    late = result["late_night"]
    console.print(f"\n[bold]Late-night commits (23:00-05:00):[/bold]")
    console.print(f"  Total commits: {late['total']}")
    console.print(f"  Late-night commits: {late['late_night_count']}")
    console.print(f"  Ratio: [{'red' if late['ratio'] > 0.3 else 'green'}]{late['ratio']:.1%}[/]")

    console.print(f"\n[bold]Output files:[/bold]")
    for name, path in result["output_files"].items():
        console.print(f"  {name}: [blue]{path}[/blue]")


def _print_summary(reports: list[dict]):
    console.print("\n[bold]Analysis Summary[/bold]\n")

    table = Table()
    table.add_column("Repository", style="cyan")
    table.add_column("Commits", justify="right")
    table.add_column("Date Range")
    table.add_column("Current Streak", justify="right", style="green")
    table.add_column("Longest Streak", justify="right", style="yellow")

    for r in reports:
        date_range = f"{r['date_range'][0]} ~ {r['date_range'][1]}" if r["date_range"][0] else "N/A"
        table.add_row(
            r["repo_name"],
            str(r["total_commits"]),
            date_range,
            f"{r['streak_current']} days",
            f"{r['streak_longest']} days",
        )

    console.print(table)

    total_commits = sum(r["total_commits"] for r in reports)
    console.print(f"\n[bold]Total commits across all repos: {total_commits}[/bold]")


if __name__ == "__main__":
    app()

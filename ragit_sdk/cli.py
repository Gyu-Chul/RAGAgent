#!/usr/bin/env python3
"""
RAGIT CLI Interface
통합 CLI 인터페이스로 모든 RAGIT 서비스를 관리
"""

import click
import sys
from typing import Optional
from .config import RagitConfig
from .process_manager import ProcessManager
from .docker_manager import DockerManager
from .logger import setup_logger


@click.group()
@click.version_option(version="0.1.0", prog_name="RAGIT")
@click.pass_context
def cli(ctx) -> None:
    """RAGIT - RAG with Gateway-Backend Architecture"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = RagitConfig()
    setup_logger()


@cli.command()
@click.option('--mode', type=click.Choice(['all', 'dev']), default='all',
              help='시작 모드 선택')
@click.pass_context
def start(ctx, mode: str) -> None:
    """Start RAGIT services"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("Starting RAGIT services...")

    if mode == 'all':
        if manager.start_all():
            click.echo("All services started successfully!")
            manager.show_service_info()
        else:
            click.echo("Error starting services.")
            sys.exit(1)
    elif mode == 'dev':
        if manager.start_dev_mode():
            click.echo("Development mode started!")
        else:
            click.echo("Failed to start development mode.")
            sys.exit(1)


@cli.command()
@click.pass_context
def stop(ctx) -> None:
    """Stop RAGIT services"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("Stopping RAGIT services...")

    if manager.stop_all():
        click.echo("All services stopped successfully!")
    else:
        click.echo("Error stopping services.")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx) -> None:
    """Check RAGIT service status"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("RAGIT service status:")
    manager.show_status()


@cli.command()
@click.pass_context
def restart(ctx) -> None:
    """Restart RAGIT services"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("Restarting RAGIT services...")

    if manager.restart_all():
        click.echo("All services restarted successfully!")
        manager.show_service_info()
    else:
        click.echo("Error restarting services.")
        sys.exit(1)


@cli.command()
@click.pass_context
def monitor(ctx) -> None:
    """Monitor RAGIT services"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("Starting RAGIT service monitoring...")
    click.echo("Press Ctrl+C to stop monitoring.")

    try:
        manager.monitor_services()
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped.")


@cli.group()
def docker() -> None:
    """Docker management commands"""
    pass


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker environment mode')
@click.pass_context
def build(ctx, mode: str) -> None:
    """Build Docker images"""
    manager = DockerManager()

    click.echo(f"Building Docker images (mode: {mode})...")

    if manager.build(mode):
        click.echo("Docker images built successfully!")
    else:
        click.echo("Failed to build Docker images!")
        sys.exit(1)


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker environment mode')
@click.pass_context
def start(ctx, mode: str) -> None:
    """Start Docker containers"""
    manager = DockerManager()

    click.echo(f"Starting Docker containers (mode: {mode})...")

    if manager.start(mode):
        click.echo("Docker containers started successfully!")
    else:
        click.echo("Failed to start Docker containers!")
        sys.exit(1)


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker environment mode')
@click.pass_context
def stop(ctx, mode: str) -> None:
    """Stop Docker containers"""
    manager = DockerManager()

    click.echo(f"Stopping Docker containers (mode: {mode})...")

    if manager.stop(mode):
        click.echo("Docker containers stopped successfully!")
    else:
        click.echo("Failed to stop Docker containers!")
        sys.exit(1)


@docker.command()
@click.option('--service', help='Check logs for specific service only')
@click.option('--follow/--no-follow', default=True, help='Follow log output in real-time')
@click.pass_context
def logs(ctx, service: Optional[str], follow: bool) -> None:
    """Check Docker container logs"""
    manager = DockerManager()

    click.echo("Checking Docker logs...")

    if manager.logs(service, follow):
        click.echo("Log check completed!")
    else:
        click.echo("Failed to check logs!")
        sys.exit(1)


@docker.command()
@click.pass_context
def ps(ctx) -> None:
    """Check Docker container status"""
    manager = DockerManager()

    click.echo("Docker container status:")

    if manager.status():
        click.echo("Status check completed!")
    else:
        click.echo("Failed to check status!")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx) -> None:
    """Display RAGIT configuration info"""
    config = ctx.obj['config']

    click.echo("RAGIT configuration:")
    click.echo(f"- Work directory: {config.work_dir}")
    click.echo(f"- Log directory: {config.log_dir}")
    click.echo(f"- Data directory: {config.data_dir}")
    click.echo(f"- Environment: {config.environment}")
    click.echo(f"- Service ports:")
    click.echo(f"  - Frontend: {config.frontend_port}")
    click.echo(f"  - Backend: {config.backend_port}")
    click.echo(f"  - Gateway: {config.gateway_port}")


def main() -> None:
    """메인 엔트리 포인트"""
    cli()


if __name__ == "__main__":
    main()
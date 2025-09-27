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
    """🚀 RAGIT - RAG with Gateway-Backend Architecture"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = RagitConfig()
    setup_logger()


@cli.command()
@click.option('--mode', type=click.Choice(['all', 'dev']), default='all',
              help='시작 모드 선택')
@click.pass_context
def start(ctx, mode: str) -> None:
    """🟢 RAGIT 서비스 시작"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("🚀 RAGIT 서비스 시작 중...")

    if mode == 'all':
        if manager.start_all():
            click.echo("✅ 모든 서비스가 성공적으로 시작되었습니다!")
            manager.show_service_info()
        else:
            click.echo("❌ 서비스 시작 중 오류가 발생했습니다.")
            sys.exit(1)
    elif mode == 'dev':
        if manager.start_dev_mode():
            click.echo("✅ 개발 모드로 시작되었습니다!")
        else:
            click.echo("❌ 개발 모드 시작 실패.")
            sys.exit(1)


@cli.command()
@click.pass_context
def stop(ctx) -> None:
    """🔴 RAGIT 서비스 중지"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("🛑 RAGIT 서비스 중지 중...")

    if manager.stop_all():
        click.echo("✅ 모든 서비스가 성공적으로 중지되었습니다!")
    else:
        click.echo("❌ 서비스 중지 중 오류가 발생했습니다.")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx) -> None:
    """📊 RAGIT 서비스 상태 확인"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("📊 RAGIT 서비스 상태:")
    manager.show_status()


@cli.command()
@click.pass_context
def restart(ctx) -> None:
    """🔄 RAGIT 서비스 재시작"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("🔄 RAGIT 서비스 재시작 중...")

    if manager.restart_all():
        click.echo("✅ 모든 서비스가 성공적으로 재시작되었습니다!")
        manager.show_service_info()
    else:
        click.echo("❌ 서비스 재시작 중 오류가 발생했습니다.")
        sys.exit(1)


@cli.command()
@click.pass_context
def monitor(ctx) -> None:
    """👀 RAGIT 서비스 모니터링"""
    config = ctx.obj['config']
    manager = ProcessManager(config)

    click.echo("👀 RAGIT 서비스 모니터링 시작...")
    click.echo("Ctrl+C로 모니터링을 중지할 수 있습니다.")

    try:
        manager.monitor_services()
    except KeyboardInterrupt:
        click.echo("\n✅ 모니터링이 중지되었습니다.")


@cli.group()
def docker() -> None:
    """🐳 Docker 관리 명령어"""
    pass


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker 환경 모드')
@click.pass_context
def build(ctx, mode: str) -> None:
    """🔨 Docker 이미지 빌드"""
    manager = DockerManager()

    click.echo(f"🔨 Docker 이미지 빌드 중 (모드: {mode})...")

    if manager.build(mode):
        click.echo("✅ Docker 이미지 빌드 완료!")
    else:
        click.echo("❌ Docker 이미지 빌드 실패!")
        sys.exit(1)


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker 환경 모드')
@click.pass_context
def start(ctx, mode: str) -> None:
    """🐳 Docker 컨테이너 시작"""
    manager = DockerManager()

    click.echo(f"🐳 Docker 컨테이너 시작 중 (모드: {mode})...")

    if manager.start(mode):
        click.echo("✅ Docker 컨테이너 시작 완료!")
    else:
        click.echo("❌ Docker 컨테이너 시작 실패!")
        sys.exit(1)


@docker.command()
@click.option('--mode', type=click.Choice(['dev', 'prod']), default='dev',
              help='Docker 환경 모드')
@click.pass_context
def stop(ctx, mode: str) -> None:
    """🛑 Docker 컨테이너 중지"""
    manager = DockerManager()

    click.echo(f"🛑 Docker 컨테이너 중지 중 (모드: {mode})...")

    if manager.stop(mode):
        click.echo("✅ Docker 컨테이너 중지 완료!")
    else:
        click.echo("❌ Docker 컨테이너 중지 실패!")
        sys.exit(1)


@docker.command()
@click.option('--service', help='특정 서비스 로그만 확인')
@click.option('--follow/--no-follow', default=True, help='실시간 로그 추적')
@click.pass_context
def logs(ctx, service: Optional[str], follow: bool) -> None:
    """📋 Docker 컨테이너 로그 확인"""
    manager = DockerManager()

    click.echo("📋 Docker 로그 확인 중...")

    if manager.logs(service, follow):
        click.echo("✅ 로그 확인 완료!")
    else:
        click.echo("❌ 로그 확인 실패!")
        sys.exit(1)


@docker.command()
@click.pass_context
def ps(ctx) -> None:
    """📊 Docker 컨테이너 상태 확인"""
    manager = DockerManager()

    click.echo("📊 Docker 컨테이너 상태:")

    if manager.status():
        click.echo("✅ 상태 확인 완료!")
    else:
        click.echo("❌ 상태 확인 실패!")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx) -> None:
    """⚙️ RAGIT 설정 정보 표시"""
    config = ctx.obj['config']

    click.echo("⚙️ RAGIT 설정 정보:")
    click.echo(f"- 작업 디렉토리: {config.work_dir}")
    click.echo(f"- 로그 디렉토리: {config.log_dir}")
    click.echo(f"- 데이터 디렉토리: {config.data_dir}")
    click.echo(f"- 환경: {config.environment}")
    click.echo(f"- 서비스 포트:")
    click.echo(f"  - Frontend: {config.frontend_port}")
    click.echo(f"  - Backend: {config.backend_port}")
    click.echo(f"  - Gateway: {config.gateway_port}")


def main() -> None:
    """메인 엔트리 포인트"""
    cli()


if __name__ == "__main__":
    main()
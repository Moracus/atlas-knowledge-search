import os
import re
import sys
from dataclasses import dataclass

import typer
from dotenv import dotenv_values, set_key

from app.core.paths import CONFIG_DIR, CONFIG_FILE


@dataclass(frozen=True)
class Field:
    key: str
    prompt: str
    default: str | None = None
    secret: bool = False
    required: bool = False


FIELDS = [
    Field("DATABASE_URL", "PostgreSQL connection URL", secret=True, required=True),
    Field("REDIS_HOST", "Redis host", default="localhost", required=True),
    Field("STORAGE_DIR", "Where Atlas stores data", default=str(CONFIG_DIR / "storage")),
    Field("EMBEDDING_PROVIDER", "Embedding provider", default="qwen"),
    Field("EMBEDDING_MODEL", "Embedding model", default="Qwen/Qwen3-Embedding-0.6B"),
    Field("EMBEDDING_DIMENSIONS", "Embedding dimensions", default="1024"),
    Field("OPENROUTER_API_KEY", "openrouter api key",  required=True),
    Field("OPENAI_API_KEY", "openai api key",  required=True)
]
KEYS = {f.key for f in FIELDS}


def load() -> dict[str, str]:
    if not CONFIG_FILE.exists():
        return {}
    return {k.upper(): v for k, v in dotenv_values(CONFIG_FILE).items() if v is not None}


def save(key: str, value: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    set_key(str(CONFIG_FILE), key, value)
    os.chmod(CONFIG_FILE, 0o600)  # the file holds DB credentials


def mask(value: str) -> str:
    return re.sub(r"(://[^:/@]+:)[^@]+(@)", r"\1***\2", value)


def is_configured() -> bool:
    cfg = load()
    return all(cfg.get(f.key) or os.environ.get(f.key) for f in FIELDS if f.required)


def run_wizard() -> None:
    current = load()
    typer.secho("Atlas configuration", bold=True)
    typer.echo(f"Saved to {CONFIG_FILE}. Press Enter to keep the current value.\n")
    for f in FIELDS:
        default = current.get(f.key, f.default)
        value = typer.prompt(f.prompt, default=default, show_default=not f.secret)
        save(f.key, str(value))
    typer.secho("\nConfiguration saved.", fg=typer.colors.GREEN)


def ensure_configured() -> None:
    if is_configured():
        return
    if not sys.stdin.isatty():
        typer.secho(
            "Atlas isn't configured. Run `atlas config` first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    typer.secho("First run: let's set up Atlas.\n", fg=typer.colors.CYAN)
    run_wizard()


config_app = typer.Typer(
    help="View or change Atlas configuration.", invoke_without_command=True
)


@config_app.callback()
def config_main(ctx: typer.Context):
    """Run without a subcommand to (re)configure interactively."""
    if ctx.invoked_subcommand is None:
        run_wizard()


@config_app.command("show")
def config_show():
    """Print the current configuration (secrets masked)."""
    cfg = load()
    for f in FIELDS:
        value = cfg.get(f.key, "(not set)")
        typer.echo(f"{f.key:<22} {mask(value) if f.secret else value}")


@config_app.command("set")
def config_set(key: str, value: str):
    """Change one value, e.g. `atlas config set REDIS_HOST localhost`."""
    key = key.upper()
    if key not in KEYS:
        typer.secho(f"Unknown key. Valid keys: {', '.join(sorted(KEYS))}", fg=typer.colors.RED)
        raise typer.Exit(1)
    save(key, value)
    typer.secho(f"{key} updated.", fg=typer.colors.GREEN)
    if key.startswith("EMBEDDING_"):
        typer.secho(
            "Existing workspaces were indexed with the old embedding settings. "
            "Run `atlas clean` then `atlas init` in each repo.",
            fg=typer.colors.YELLOW,
        )


@config_app.command("path")
def config_path():
    """Print where the config file lives."""
    typer.echo(CONFIG_FILE)
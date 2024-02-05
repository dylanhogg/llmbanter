from datetime import datetime
from time import sleep
from typing import Optional

import typer
from loguru import logger
from rich import print
from tqdm import tqdm
from typing_extensions import Annotated

from .library import consts, env, log
from .library.classes import AppUsageException

typer_app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(f"{consts.package_name} version: {consts.version}")
        raise typer.Exit()


@typer_app.command()
def run(
    llm1: Annotated[str, typer.Argument(help="Name of the first Large Language Model")],
    llm2: Annotated[str, typer.Argument(help="Name of the second Large Language Model")],
    llm_use_localhost: Annotated[
        int, typer.Option(help="LLM use localhost:8081 instead of openai")
    ] = consts.default_llm_use_localhost,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", help=f"Display {consts.package_name} version", callback=version_callback),
    ] = None,
) -> None:
    """
    Command entry point
    """

    try:
        log.configure()
        example_usage = f"Example usage: [bold green]{consts.package_name}[/bold green]"

        logger.info(f"Start {consts.package_name}, {llm1=}, {llm2=}")

        llm_api_key = env.get("OPENAI_API_KEY", "")
        if not llm_use_localhost and not llm_api_key:
            raise AppUsageException(
                "Expected an environment variable 'OPENAI_API_KEY' to be set to use OpenAI API."
                "\nSee the OpenAI docs for more info: https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key"
                "\nAlternatively you can use the '--llm_use_localhost 1' argument to use a local LLM server."
            )

        start = datetime.now()

        # TODO: do the stuff
        for _ in tqdm(range(5)):
            sleep(0.1)

        took = datetime.now() - start
        print("")
        print(f"[bold green]{consts.package_name} finished, took {took.total_seconds()}s.[/bold green]")

        raise typer.Exit(0)

    except AppUsageException as ex:
        print(example_usage)
        print(f"[bold red]{str(ex)}[/bold red]")
        print("")
        print(f"For more information, try '{consts.package_name} --help'.")
        logger.exception(ex)

    except typer.Exit as ex:
        if ex.exit_code == 0:
            print()
            print(
                f"[bold green]Goodbye and thanks for using {consts.package_name}! Please consider starring the project on github: https://github.com/dylanhogg/{consts.package_name}[/bold green]"
            )
            return
        print(example_usage)
        print(f"[bold red]Unexpected error code: {str(ex)}[/bold red]")
        print("")
        print(f"For more information, try '{consts.package_name} --help'.")
        logger.exception(ex)

    except Exception as ex:
        print(example_usage)
        print(f"[bold red]Unexpected exception: {str(ex)}[/bold red]")
        print("")
        print(f"For more information, try '{consts.package_name} --help'.")
        logger.exception(ex)

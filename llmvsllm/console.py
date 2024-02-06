from datetime import datetime
from typing import Optional

import typer
from loguru import logger
from rich import print
from typing_extensions import Annotated

from llmvsllm.arena.conversation import Conversation
from llmvsllm.library import consts, env, log
from llmvsllm.library.classes import AppUsageException

typer_app = typer.Typer()


def version_callback(value: bool):
    if value:
        print(f"{consts.package_name} version: {consts.version}")
        raise typer.Exit()


@typer_app.command()
def run(
    bot1: Annotated[str, typer.Argument(help="Name of the first bot")],
    bot2: Annotated[str, typer.Argument(help="Name of the second bot")],
    model1: Annotated[str, typer.Argument(help="Model of the first bot")] = consts.default_llm_model,
    model2: Annotated[str, typer.Argument(help="Model of the second bot")] = consts.default_llm_model,
    speak: Annotated[bool, typer.Option(help="Enable speaking")] = False,
    llm_use_localhost: Annotated[
        int, typer.Option(help="LLM use localhost:8081 instead of openai")
    ] = consts.default_llm_use_localhost,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", help=f"Display {consts.package_name} version", callback=version_callback),
    ] = None,
) -> None:
    """
    App entry point
    """
    log.configure()
    logger.info(f"Start {consts.package_name}, {bot1=}, {bot2=}, {speak=}")
    example_usage = f"Example usage: [bold green]{consts.package_name} python_language_evangelist java_language_evangelist[/bold green]"

    try:
        llm_api_key = env.get("OPENAI_API_KEY", "")
        if not llm_use_localhost and not llm_api_key:
            raise AppUsageException(
                "Expected an environment variable 'OPENAI_API_KEY' to be set to use OpenAI API."
                "\nSee the OpenAI docs for more info: https://platform.openai.com/docs/quickstart/step-2-setup-your-api-key"
                "\nAlternatively you can use the '--llm_use_localhost 1' argument to use a local LLM server."
            )

        start = datetime.now()
        conversation = Conversation(bot1=bot1, bot2=bot2, model1=model1, model2=model2, speak=speak)
        conversation.start()
        took = datetime.now() - start

        print("")
        print(f"[bold green]{consts.package_name} finished, took {took.total_seconds()}s.[/bold green]")

        raise typer.Exit(0)

    except AppUsageException as ex:
        print(example_usage)
        print(f"[bold red]{str(ex)}[/bold red]")
        print("")
        print(f"For more information, try '{consts.package_name} --help'.")
        logger.info(ex)

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

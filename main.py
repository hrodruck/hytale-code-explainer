# main.py
import argparse
import os
import sys

def run_discord():
    from src.interfaces.discord_bot import bot  # Adjust if your path differs (e.g., discord_bot if flat)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    
    print("Starting Discord bot...")
    bot.run(token)


def run_cli():
    from src.interfaces.cli import main  # Adjust if your path differs (e.g., cli if flat)

    print("Starting CLI...")
    main()


def main():
    parser = argparse.ArgumentParser(
        description="Hytale Codebase Assistant – run Discord bot or CLI"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True, help="Interface to run")

    discord_parser = subparsers.add_parser("discord", help="Run the Discord bot")
    cli_parser = subparsers.add_parser("cli", help="Run the interactive CLI")

    args = parser.parse_args()

    if args.mode == "discord":
        run_discord()
    elif args.mode == "cli":
        run_cli()


if __name__ == "__main__":
    main()


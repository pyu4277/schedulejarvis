#!/usr/bin/env python3
import click
import logging
import json
from datetime import datetime
from src.notion_client import NotionClient
from src.google_calendar_client import GoogleCalendarClient
from src.claude_parser import ClaudeParser
from src.sync_manager import SyncManager
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Schedule Jarvis - Notion + Google Calendar Sync Tool"""
    pass


@cli.command()
@click.option(
    "--text",
    prompt="Enter raw schedule text",
    help="Raw schedule text to parse",
)
@click.option(
    "--page-id",
    help="Notion page ID to update",
)
def parse(text, page_id):
    """Parse raw text and create schedule"""
    try:
        parser = ClaudeParser(config.ANTHROPIC_API_KEY)
        notion = NotionClient(config.NOTION_API_KEY, config.NOTION_DATABASE_ID)
        calendar = GoogleCalendarClient(config.TARGET_CALENDAR_ID)
        sync_manager = SyncManager(notion, calendar, parser)

        logger.info("Processing raw input...")
        result = sync_manager.process_raw_input(text, page_id)

        click.echo("\n✅ Schedule created successfully!")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Error processing input")


@cli.command()
@click.option(
    "--page-id",
    required=True,
    help="Notion page ID to sync",
)
def sync_notion_to_calendar(page_id):
    """Sync Notion page to Google Calendar"""
    try:
        parser = ClaudeParser(config.ANTHROPIC_API_KEY)
        notion = NotionClient(config.NOTION_API_KEY, config.NOTION_DATABASE_ID)
        calendar = GoogleCalendarClient(config.TARGET_CALENDAR_ID)
        sync_manager = SyncManager(notion, calendar, parser)

        logger.info(f"Syncing Notion page {page_id} to calendar...")
        result = sync_manager.sync_notion_to_calendar(page_id)

        click.echo("\n✅ Sync completed!")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Error syncing Notion to calendar")


@cli.command()
def list_notion_pages():
    """List all Notion pages in database"""
    try:
        notion = NotionClient(config.NOTION_API_KEY, config.NOTION_DATABASE_ID)

        logger.info("Fetching Notion pages...")
        pages = notion.get_all_pages()

        click.echo(f"\nFound {len(pages)} pages:\n")
        for i, page in enumerate(pages, 1):
            title = notion.get_property_value(page, config.NOTION_FIELDS["title"])
            page_id = page.get("id")
            click.echo(f"{i}. {title} (ID: {page_id})")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Error listing Notion pages")


@cli.command()
@click.option("--days", default=30, help="Number of days to show")
def list_calendar_events(days):
    """List upcoming calendar events"""
    try:
        calendar = GoogleCalendarClient(config.TARGET_CALENDAR_ID)

        logger.info(f"Fetching calendar events for next {days} days...")
        from datetime import timedelta

        now = datetime.utcnow()
        future = (now + timedelta(days=days)).isoformat() + "Z"
        now = now.isoformat() + "Z"

        events = calendar.list_events(time_min=now, time_max=future)

        click.echo(f"\nFound {len(events)} events:\n")
        for i, event in enumerate(events, 1):
            title = event.get("summary", "No title")
            start = event.get("start", {}).get("dateTime", "N/A")
            click.echo(f"{i}. {title} - {start}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Error listing calendar events")


@cli.command()
@click.option(
    "--text",
    prompt="Enter raw schedule text",
    help="Raw schedule text to parse",
)
def test_parser(text):
    """Test the Claude parser"""
    try:
        parser = ClaudeParser(config.ANTHROPIC_API_KEY)

        logger.info("Testing parser...")
        result = parser.parse_schedule(text)

        click.echo("\n✅ Parsing successful!")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Error in parser")


if __name__ == "__main__":
    cli()

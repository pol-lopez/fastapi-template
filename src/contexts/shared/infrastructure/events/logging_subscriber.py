from loguru import logger

from src.contexts.shared.domain.events import DomainEvent


async def log_domain_event(event: DomainEvent) -> None:
    logger.bind(
        event_type=type(event).__name__,
        occurred_on=str(event.occurred_on),
    ).info("Domain event: {event_type}", event_type=type(event).__name__)

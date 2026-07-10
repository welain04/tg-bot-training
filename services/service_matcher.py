from domain.models.service import Service


def match_service_in_text(text: str, services: list[Service]) -> Service | None:
    text_lower = text.lower()
    matched = [service for service in services if service.name.lower() in text_lower]
    if len(matched) == 1:
        return matched[0]
    if not matched:
        return None

    matched.sort(key=lambda service: len(service.name), reverse=True)
    if len(matched) >= 2 and len(matched[0].name) > len(matched[1].name):
        return matched[0]
    return None

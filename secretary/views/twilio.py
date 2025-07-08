from django.http import HttpResponse


def sms_reply(request) -> HttpResponse:
    """SMS endpoint not yet migrated to the new openai-agents framework."""
    return HttpResponse("Not implemented", status=501)

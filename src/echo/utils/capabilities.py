import json
from typing import TypedDict

from pydantic import TypeAdapter, ValidationError


class InvalidCapabilitiesError(ValueError):
    pass


class SalesforceCouponPayload(TypedDict):
    interaction_campaign_id: str


class IgnoreCooldownPayload(TypedDict):
    ignore_cooldown: bool


class Capabilities(TypedDict, total=False):
    send_salesforce_coupon: SalesforceCouponPayload
    ignore_cooldown: IgnoreCooldownPayload


CapabilitiesAdapter: TypeAdapter[Capabilities] = TypeAdapter(Capabilities)


def parse_capabilities(raw: str | None) -> Capabilities:
    if not raw:
        return Capabilities()

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise InvalidCapabilitiesError("capabilities must be a JSON object")

        return CapabilitiesAdapter.validate_python(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InvalidCapabilitiesError(str(exc)) from exc

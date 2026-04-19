from typing import TypedDict


class SalesforceCouponPayload(TypedDict):
    interacion_campaign_id: str

class IgnoreCooldownPayload(TypedDict):
    ignore_cooldown: bool

class Capabilities(TypedDict, total=False):
    send_salesforce_coupon: SalesforceCouponPayload
    ignore_cooldown: IgnoreCooldownPayload

from pydantic import BaseModel, ConfigDict


class SalesforceCouponPayload(BaseModel):
    interaction_campaign_id: str


class Capabilities(BaseModel):
    send_salesforce_coupon: SalesforceCouponPayload | None = None
    ignore_cooldown: bool = False

    model_config = ConfigDict(extra="forbid")

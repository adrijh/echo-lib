from pydantic import BaseModel, ConfigDict, Field


class SalesforceCouponPayload(BaseModel):
    interaction_campaign_id: str


class CallCooldown(BaseModel):
    ignore: bool = False
    ttl_days: int = 60

    @property
    def ttl_seconds(self) -> int:
        return self.ttl_days * 86400


class RunSteps(BaseModel):
    context: bool = True
    evaluations: bool = True
    asesoria: bool = True


class Capabilities(BaseModel):
    send_salesforce_coupon: SalesforceCouponPayload | None = None
    cooldown: CallCooldown | None = None
    steps: RunSteps = Field(default_factory=RunSteps)

    model_config = ConfigDict(extra="ignore")

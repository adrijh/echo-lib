from pydantic import BaseModel, ConfigDict, Field


class ArgumentarioRequest(BaseModel):
    study_id: str


class Characteristics(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    credits: str | None = Field(None, alias="Créditos")
    duration: str | None = Field(None, alias="Duración")
    methodology: str | None = Field(None, alias="Metodología")
    next_intake: str | None = Field(None, alias="Próxima convocatoria")


class Profile(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    title: str | None = None
    perfiles: str | None = None
    necesidades_motivaciones: str | None = None
    argumentos_especificos: str | None = None


class SellingArguments(BaseModel):
    model_config = ConfigDict(extra="allow")

    general: str | None = None
    profiles: list[Profile] = Field(default_factory=list)


class Closing(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    price_defense: str | None = Field(None, alias="Defensa del precio")
    tips: str | None = Field(None, alias="Tips de cierre")


class Argumentario(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    name: str | None = None
    faculty: str | None = None
    region: str | None = None
    description: str | None = None
    characteristics: Characteristics = Field(default_factory=Characteristics)
    access_requirements: str | None = None
    selling_arguments: SellingArguments = Field(default_factory=SellingArguments)
    study_plan: str | None = None
    closing: Closing = Field(default_factory=Closing)
    faq: str | None = None


class ArgumentariosListResponse(BaseModel):
    items: list[Argumentario]

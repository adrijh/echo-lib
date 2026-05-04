from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SalesforceDataRequest(BaseModel):
    opportunity_id: str


class SellLeversResponse(BaseModel):
    levers: list[str]


class AgeAndSalary(BaseModel):
    model_config = ConfigDict(extra="allow")

    age: int | None = None
    min_range_salary: int | None = None
    max_range_salary: int | None = None
    reasoning: str | None = None


class Experience(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str | None = None
    company: str | None = None
    duration_years: float | None = None
    location: str | None = None


class Motivation(BaseModel):
    model_config = ConfigDict(extra="allow")

    motivation: str | None = None
    reasoning: str | None = None


class Lever(BaseModel):
    model_config = ConfigDict(extra="allow")

    palanca: str | None = None
    description: str | None = None
    reasoning: str | None = None


class LinkedInProfileResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    location: str | None = None
    occupation: str | None = None
    age_and_salary: AgeAndSalary | None = None
    education: list[Any] | None = None
    experiences: list[Experience] | None = None
    summary_experience: str | None = None
    motivations: list[Motivation] | None = None
    palancas: list[Lever] | None = None
    argumentacion_sugerida: list[Lever] | None = None


class AcademicFormation(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    titulo: str | None = None
    tipo_titulo: str | None = Field(None, alias="tipoTitulo")
    estado: str | None = None


class AIDetailsData(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    oportunidad_id: str | None = Field(None, alias="oportunidadId")
    edad: str | None = None
    formacion_academica: list[AcademicFormation] | None = Field(None, alias="formacionAcademica")
    experiencia_profesional: list[str] | None = Field(None, alias="experienciaProfesional")
    motivaciones_necesidades_estudiante: list[str] | None = Field(None, alias="motivacionesNecesidadesEstudiante")
    motivos_no_interes: str | None = Field(None, alias="motivosNoInteres")

    @field_validator("experiencia_profesional", mode="before")
    @classmethod
    def _normalize_experiencia_profesional(cls, v: Any) -> Any:
        if not isinstance(v, list):
            return v
        normalized: list[str] = []
        for item in v:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(" | ".join(str(x) for x in item.values() if x is not None))
            else:
                normalized.append(str(item))
        return normalized


class AIDetailsResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    error_code: int | None = Field(None, alias="error_code")
    error_message: str | None = Field(None, alias="error_message")
    response: AIDetailsData | None = None

from pydantic import BaseModel, Field
from typing import List

class HealthResponse(BaseModel):
    status: str = Field(description="The health status of the service", examples=["ok"])

class InfoResponse(BaseModel):
    product_name: str = Field(description="The official product name", examples=["Inevitable"])
    tagline: str = Field(description="The product tagline", examples=["Don't trust the patch. Prove it."])
    version: str = Field(description="The current version", examples=["0.1.0"])
    capabilities: List[str] = Field(description="List of supported capabilities")

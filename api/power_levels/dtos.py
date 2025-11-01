from pydantic import BaseModel, Field

class PowerLevel(BaseModel):
    combat: int = Field(..., ge=0, le=3000)
    objectives: int = Field(..., ge=0, le=2500)
    vision: int = Field(..., ge=0, le=1500)
    economy: int = Field(..., ge=0, le=1500)
    clutch: int = Field(..., ge=0, le=1500)

    total: int = Field(..., ge=0, le=10000, description="Sum of all subscores (0–10000)")
class CreatePowerLevelDto(PowerLevel):
    match_id: str = Field(..., description="Match identifier")
    puuid: str = Field(..., description="Player unique identifier")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "match_id": "NA1_1234567890",
                "puuid": "abcd-efgh-ijkl-1234",
                "combat": 2400,
                "objectives": 1800,
                "vision": 950,
                "economy": 1200,
                "clutch": 1150,
                "total": 7500
            }
        },
    }
    

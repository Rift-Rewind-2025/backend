from pydantic import BaseModel, Field
from typing import Optional
from libs.common.constants.league_constants import RolePosition

class PowerLevelMetrics(BaseModel):
    # Champion info
    champion_name: str
    role_position: RolePosition
    champ_level: int = Field(..., ge=1)

    # Game context
    game_duration: int = Field(..., gt=0)  # seconds
    win: bool

    # Core stats
    kills: int = Field(..., ge=0)
    deaths: int = Field(..., ge=0)
    assists: int = Field(..., ge=0)

    # Damage
    total_damage_dealt: int = Field(..., ge=0)
    total_damage_taken: int = Field(..., ge=0)
    damage_per_minute: Optional[float] = Field(None, ge=0)
    team_damage_percentage: Optional[float] = Field(None, ge=0, le=1)
    damage_taken_on_team_percentage: Optional[float] = Field(None, ge=0, le=1)

    # Economy
    total_gold: Optional[int] = Field(None, ge=0)
    gold_per_minute: Optional[float] = Field(None, ge=0)
    cs_count: Optional[int] = Field(None, ge=0)

    # Vision
    vision_score: Optional[float] = Field(None, ge=0)
    wards_placed: Optional[int] = Field(None, ge=0)
    wards_destroyed: Optional[int] = Field(None, ge=0)
    vision_score_per_minute: Optional[float] = Field(None, ge=0)

    # Objectives
    dragons_killed: Optional[int] = Field(None, ge=0)
    barons_killed: Optional[int] = Field(None, ge=0)
    heralds_killed: Optional[int] = Field(None, ge=0)
    turrets_destroyed: Optional[int] = Field(None, ge=0)
    turret_plates_taken: Optional[int] = Field(None, ge=0)

    # Mechanical skill
    skillshots_hit: Optional[int] = Field(None, ge=0)
    skillshot_accuracy: Optional[float] = Field(None, ge=0, le=1)
    skillshots_dodged: Optional[int] = Field(None, ge=0)
    immobilize_and_kill: Optional[int] = Field(None, ge=0)

    # Clutch moments
    solo_kills: Optional[int] = Field(None, ge=0)
    outnumbered_kills: Optional[int] = Field(None, ge=0)
    double_kills: Optional[int] = Field(None, ge=0)
    triple_kills: Optional[int] = Field(None, ge=0)
    quadra_kills: Optional[int] = Field(None, ge=0)
    penta_kills: Optional[int] = Field(None, ge=0)
    killing_sprees: Optional[int] = Field(None, ge=0)
    largest_killing_spree: Optional[int] = Field(None, ge=0)
    first_blood_taken: Optional[bool] = None
    first_blood_assist: Optional[bool] = None

    # Teamwork
    kill_participation: Optional[float] = Field(None, ge=0, le=1)
    full_team_takedowns: Optional[int] = Field(None, ge=0)
    save_ally_from_death: Optional[int] = Field(None, ge=0)
    pick_kill_with_ally: Optional[int] = Field(None, ge=0)
    kill_after_hidden: Optional[int] = Field(None, ge=0)

    # Survivability
    longest_time_living: Optional[int] = Field(None, ge=0)
    time_spent_dead: Optional[int] = Field(None, ge=0)
    survived_three_immobilizes: Optional[int] = Field(None, ge=0)
    deaths_by_enemy_champs: Optional[int] = Field(None, ge=0)

    # Control
    time_ccing_others: Optional[int] = Field(None, ge=0)
    enemy_immobilizations: Optional[int] = Field(None, ge=0)

    # Progression
    legendary_items_count: Optional[int] = Field(None, ge=0)
    max_level_lead: Optional[int] = Field(None, ge=0)
    takedowns_first_10min: Optional[int] = Field(None, ge=0)

    # Special
    flawless_aces: Optional[int] = Field(None, ge=0)
    perfect_game: Optional[bool] = None

class CreatePowerLevelMetricsDto(PowerLevelMetrics):
    # Foreign keys / identity
    match_id: str
    puuid: str

    model_config = {
        "from_attributes": True,  # v2 replacement for orm_mode
        "json_schema_extra": {
            "example": {
                "match_id": "NA1_1234567890",
                "puuid": "abcd-efgh-ijkl-1234",
                "champion_name": "Ahri",
                "role_position": "MIDDLE",
                "champ_level": 18,
                "game_duration": 1800,
                "win": True,
                "kills": 10,
                "deaths": 2,
                "assists": 8,
                "total_damage_dealt": 25000,
                "total_damage_taken": 15000,
                "team_damage_percentage": 0.32,
                "total_gold": 14000,
                "cs_count": 250,
                "vision_score": 25.5,
                "skillshots_hit": 120,
                "skillshot_accuracy": 0.72,
                "solo_kills": 2,
                "perfect_game": False
            }
        },
    }
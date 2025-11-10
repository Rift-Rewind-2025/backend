from pydantic import BaseModel
from typing import Optional

class CreateUserDto(BaseModel):
    puuid: str
    game_name: str
    tag_line: str
    
class UpdateUserDto(BaseModel):
    game_name: Optional[str] = None
    tag_line: Optional[str] = None
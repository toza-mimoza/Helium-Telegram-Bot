from .BaseModel import BaseModel

class Hotspot(BaseModel):
    def __init__(self, hotspot_address: str, animal_name: str, fk_owner_address: str) -> None:
        super().__init__()
        self.animal_name = animal_name
        self.hotspot_address = hotspot_address
        self.owner_address = fk_owner_address

    def __hash__(self) -> int:
        return hash(self.hotspot_address, self.owner_address)
    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and self.hotspot_address == __o.hotspot_address

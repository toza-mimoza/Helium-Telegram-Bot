from typing import List
from .BaseModel import BaseModel
from util.constants import DbConstants

class Owner(BaseModel):
    '''
    Hotspot owner class
    '''
    def __init__(self, helium_address, user_id) -> None:
        # owner id is the helium account address 
        super().__init__(DbConstants.TREE_OWNERS, custom_uuid=helium_address)
        self.helium_address = helium_address # PK
        self.telegram_user_id = user_id

    def __hash__(self) -> int:
        return hash(self.helium_address, self.telegram_user_id)
    
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, self.__class__) and self.helium_address == __o.helium_address

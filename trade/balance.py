from dataclasses import dataclass, asdict
from database.services import save_balance

@dataclass()
class Balance:
    current_balance: float

    def save_balance(self):
        pass
        # save to mongo

    def set_balance(self, new_balance):
        self.current_balance = float("{:.2f}".format(new_balance))
        self.save()


    def read_balance(self):
        pass
        # call mongo
        # self.current_balance = response from mongo

    def calculate_possible_order_volume(self, price):
        volume = float("{:.3f}".format(self.current_balance / 4 / price ))
        return volume

    def save(self):
        to_save = asdict(self)
        save_balance(to_save)
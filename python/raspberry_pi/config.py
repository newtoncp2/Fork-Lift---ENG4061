class AppState:
    def __init__(self):
        self._is_autonomous = False

    # Using properties lets you add logic/validation later if needed
    @property
    def is_autonomous(self):
        return self._is_autonomous

    @is_autonomous.setter
    def is_autonomous(self, value):
        if isinstance(value, bool):
            self._is_autonomous = value
        else:
            raise ValueError("is_autonomous must be a boolean value")


config = AppState()

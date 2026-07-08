class AppState:
    def __init__(self):
        self._is_autonomous = False
        self._estado = "manual"  # Default state is manual
        self._etapa_busca = 0
        self._etapa_aprox = 0

    # Using properties lets you add logic/validation later if needed
    @property
    def is_autonomous(self):
        return self._is_autonomous
    
    @property
    def estado(self):
        return self._estado
    
    @property
    def etapa_busca(self):
        return self._etapa_busca
    
    @property
    def etapa_aprox(self):
        return self._etapa_aprox

    @is_autonomous.setter
    def is_autonomous(self, value):
        if isinstance(value, bool):
            self._is_autonomous = value
        else:
            raise ValueError("is_autonomous must be a boolean value")
        
    @estado.setter
    def estado(self, value):
        if isinstance(value, str):
            self._estado = value
        else:
            raise ValueError("estado must be a string value")
        
    @etapa_busca.setter
    def etapa_busca(self, value):
        if isinstance(value, int):
            self._etapa_busca = value
        else:
            raise ValueError("etapa_busca must be a int value")

    @etapa_aprox.setter
    def etapa_aprox(self, value):
        if isinstance(value, int):
            self._etapa_aprox = value
        else:
            raise ValueError("etapa_aprox must be a int value")

config = AppState()
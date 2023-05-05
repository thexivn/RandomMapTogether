class GameCancelledException(Exception):
    def __init__(self, message="Game was cancelled"):
        super().__init__(message)

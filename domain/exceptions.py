class ConfigFieldException(Exception):
    def __init__(self, exception):
        self.message = f"There is no such field in configuration: {exception}"

    def __str__(self):
        return self.message


class NoPeersException(Exception):
    def __init__(self):
        self.message = f"There is no peers for that file"

    def __str__(self):
        return self.message


class DirectoriesCreationException(Exception):
    def __init__(self):
        self.message = f"Faild to create directories"

    def __str__(self):
        return self.message
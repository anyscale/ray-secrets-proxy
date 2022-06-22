from cryptography.fernet import Fernet
from time import time

class RaySecret:
    def __init__(self, secret_name, secret, ttl=-1, metadata={}) -> None:
        self.create_timestamp = int(time())
        self.secret_name = secret_name
        self.metadata = metadata
        self.ttl = ttl
        self.__key = Fernet.generate_key()
        self.__secret = Fernet(self.__key).encrypt(secret.encode())
        return

    def __str__(self):
        return self.secret_name + ": ***********"

    def __repr__(self):
        return str(self)

    def value(self):
        return Fernet(self.__key).decrypt(self.__secret).decode()

    def is_expired(self):
        if self.ttl == -1 or (int(time()) - self.create_timestamp) <= self.ttl:
            return False
        return True

from cryptography.fernet import Fernet
from django.conf import settings


class FernetEncryption:
    """
    A class to handle encryption and decryption using Fernet.
    This class ensures that for a given key, the instance is created only once.
    """
    _instances = {}

    def __new__(cls, key: str = None):
        if key is None:
            key = settings.FERNET_KEY

        if key not in cls._instances:
            instance = super().__new__(cls)
            instance.key = key.encode()
            instance.fernet = Fernet(instance.key)
            cls._instances[key] = instance
        
        return cls._instances[key]

    def encrypt(self, data: str) -> str:
        """
        Encrypts a string.
        """
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypts a string.
        """
        if not encrypted_data:
            return ""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

"""
Criptografia do mapeamento de anonimização.
Autor: Matheus C. Pestana

Usa Fernet (AES-128-CBC) com chave derivada de senha via PBKDF2.
"""

import json
import base64
import os
from typing import Dict

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _derive_key(password: str, salt: bytes) -> bytes:
    """
    Deriva uma chave Fernet a partir de uma senha.
    
    Args:
        password: Senha do usuário
        salt: Salt para derivação
    
    Returns:
        Chave de 32 bytes codificada em base64
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # Recomendado para 2024+
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_mapping(mapping: Dict[str, Dict[str, str]], password: str) -> bytes:
    """
    Criptografa o mapeamento de anonimização.
    
    Args:
        mapping: Dicionário de mapeamentos (original -> falso)
        password: Senha para criptografia
    
    Returns:
        Bytes do mapeamento criptografado (salt + dados)
    """
    # Gera salt aleatório
    salt = os.urandom(16)
    
    # Deriva chave da senha
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    
    # Serializa e criptografa
    json_data = json.dumps(mapping, ensure_ascii=False).encode('utf-8')
    encrypted = fernet.encrypt(json_data)
    
    # Retorna salt + dados criptografados
    return salt + encrypted


def decrypt_mapping(encrypted_data: bytes, password: str) -> Dict[str, Dict[str, str]]:
    """
    Descriptografa o mapeamento de anonimização.
    
    Args:
        encrypted_data: Bytes criptografados (salt + dados)
        password: Senha para descriptografia
    
    Returns:
        Dicionário de mapeamentos
    
    Raises:
        ValueError: Se a senha estiver incorreta ou dados corrompidos
    """
    # Extrai salt e dados
    salt = encrypted_data[:16]
    encrypted = encrypted_data[16:]
    
    # Deriva chave da senha
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    
    try:
        # Descriptografa
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode('utf-8'))
    except InvalidToken:
        raise ValueError("Senha incorreta ou dados corrompidos")
    except json.JSONDecodeError:
        raise ValueError("Dados corrompidos - não é JSON válido")


def save_encrypted_mapping(
    mapping: Dict[str, Dict[str, str]], 
    password: str, 
    filepath: str
) -> None:
    """
    Salva mapeamento criptografado em arquivo.
    
    Args:
        mapping: Dicionário de mapeamentos
        password: Senha para criptografia
        filepath: Caminho do arquivo de saída
    """
    encrypted = encrypt_mapping(mapping, password)
    with open(filepath, 'wb') as f:
        f.write(encrypted)


def load_encrypted_mapping(filepath: str, password: str) -> Dict[str, Dict[str, str]]:
    """
    Carrega mapeamento criptografado de arquivo.
    
    Args:
        filepath: Caminho do arquivo
        password: Senha para descriptografia
    
    Returns:
        Dicionário de mapeamentos
    """
    with open(filepath, 'rb') as f:
        encrypted = f.read()
    return decrypt_mapping(encrypted, password)


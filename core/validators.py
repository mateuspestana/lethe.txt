"""
Validadores de documentos brasileiros (CPF, RG) e datas.
Autor: Matheus C. Pestana
"""

import re
from typing import List, Tuple
from datetime import datetime


def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF brasileiro usando o algoritmo oficial de dígitos verificadores.
    
    Args:
        cpf: String contendo o CPF (pode conter pontos e traço)
    
    Returns:
        True se o CPF é válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)
    
    # CPF deve ter 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2


def validate_rg(rg: str) -> bool:
    """
    Valida formato básico de RG brasileiro.
    
    Nota: RGs variam muito entre estados, então a validação é básica.
    Aceita formatos como: XX.XXX.XXX-X ou XXXXXXXXX
    
    Args:
        rg: String contendo o RG
    
    Returns:
        True se o formato é válido, False caso contrário
    """
    # Remove caracteres não alfanuméricos
    rg_clean = re.sub(r'[^0-9Xx]', '', rg)
    
    # RG geralmente tem entre 7 e 9 dígitos
    if len(rg_clean) < 7 or len(rg_clean) > 9:
        return False
    
    return True


def extract_cpfs(text: str) -> List[Tuple[str, int, int]]:
    """
    Extrai CPFs de um texto.
    
    Args:
        text: Texto para buscar CPFs
    
    Returns:
        Lista de tuplas (cpf, posição_início, posição_fim)
    """
    # Padrões de CPF: 000.000.000-00 ou 00000000000
    patterns = [
        r'\d{3}\.\d{3}\.\d{3}-\d{2}',  # Formato com pontuação
        r'\d{11}',  # Formato apenas números
    ]
    
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            cpf = match.group()
            if validate_cpf(cpf):
                results.append((cpf, match.start(), match.end()))
    
    # Remove duplicatas mantendo a primeira ocorrência
    seen = set()
    unique_results = []
    for cpf, start, end in results:
        cpf_clean = re.sub(r'\D', '', cpf)
        if cpf_clean not in seen:
            seen.add(cpf_clean)
            unique_results.append((cpf, start, end))
    
    return unique_results


def extract_rgs(text: str) -> List[Tuple[str, int, int]]:
    """
    Extrai RGs de um texto.
    
    Args:
        text: Texto para buscar RGs
    
    Returns:
        Lista de tuplas (rg, posição_início, posição_fim)
    """
    # Padrões de RG: XX.XXX.XXX-X ou variações
    patterns = [
        r'\d{2}\.\d{3}\.\d{3}-[\dXx]',  # Formato SP: 00.000.000-0
        r'\d{1,2}\.\d{3}\.\d{3}',  # Formato sem dígito verificador
    ]
    
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            rg = match.group()
            if validate_rg(rg):
                results.append((rg, match.start(), match.end()))
    
    return results


def extract_birth_dates(text: str) -> List[Tuple[str, int, int, datetime]]:
    """
    Extrai datas de nascimento de um texto.
    
    Args:
        text: Texto para buscar datas
    
    Returns:
        Lista de tuplas (data_string, posição_início, posição_fim, datetime_obj)
    """
    # Padrões de data: DD/MM/AAAA, DD-MM-AAAA, DD.MM.AAAA
    patterns = [
        (r'\d{2}/\d{2}/\d{4}', '%d/%m/%Y'),
        (r'\d{2}-\d{2}-\d{4}', '%d-%m-%Y'),
        (r'\d{2}\.\d{2}\.\d{4}', '%d.%m.%Y'),
    ]
    
    results = []
    current_year = datetime.now().year
    
    for pattern, date_format in patterns:
        for match in re.finditer(pattern, text):
            date_str = match.group()
            try:
                date_obj = datetime.strptime(date_str, date_format)
                # Considera como data de nascimento se a pessoa tiver entre 0 e 120 anos
                age = current_year - date_obj.year
                if 0 <= age <= 120:
                    results.append((date_str, match.start(), match.end(), date_obj))
            except ValueError:
                continue
    
    return results


def generate_valid_cpf() -> str:
    """
    Gera um CPF válido aleatório.
    
    Returns:
        CPF no formato XXX.XXX.XXX-XX
    """
    import random
    
    # Gera 9 dígitos aleatórios
    cpf = [random.randint(0, 9) for _ in range(9)]
    
    # Calcula primeiro dígito verificador
    soma = sum(cpf[i] * (10 - i) for i in range(9))
    resto = soma % 11
    cpf.append(0 if resto < 2 else 11 - resto)
    
    # Calcula segundo dígito verificador
    soma = sum(cpf[i] * (11 - i) for i in range(10))
    resto = soma % 11
    cpf.append(0 if resto < 2 else 11 - resto)
    
    # Formata
    cpf_str = ''.join(map(str, cpf))
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"


def generate_valid_rg() -> str:
    """
    Gera um RG válido aleatório (formato SP).
    
    Returns:
        RG no formato XX.XXX.XXX-X
    """
    import random
    
    # Gera 8 dígitos aleatórios
    rg = [random.randint(0, 9) for _ in range(8)]
    
    # Último dígito pode ser X
    last_digit = random.choice([str(i) for i in range(10)] + ['X'])
    
    rg_str = ''.join(map(str, rg))
    return f"{rg_str[:2]}.{rg_str[2:5]}.{rg_str[5:8]}-{last_digit}"


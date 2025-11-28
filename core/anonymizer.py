"""
Anonimizador de dados sensíveis.
Autor: Matheus C. Pestana

Gera dados falsos e substitui no texto mantendo coesão.
"""

import re
import random
from typing import Dict, Set, Tuple
from datetime import datetime, timedelta
from faker import Faker

from .validators import generate_valid_cpf, generate_valid_rg
from .entity_detector import EntityDetector, DetectedEntity


class Anonymizer:
    """Anonimizador de dados sensíveis em textos."""
    
    def __init__(self, seed: int = None):
        """
        Inicializa o anonimizador.
        
        Args:
            seed: Seed para reprodutibilidade (opcional)
        """
        self.faker = Faker('pt_BR')
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        
        self.detector = EntityDetector()
        self.mapping: Dict[str, Dict[str, str]] = {
            'persons': {},
            'cpfs': {},
            'rgs': {},
            'dates': {},
        }
    
    def generate_replacements(self, entities: Dict[str, list]) -> Dict[str, Dict[str, str]]:
        """
        Gera mapeamento de valores originais para falsos.
        
        Args:
            entities: Dicionário de entidades detectadas
        
        Returns:
            Dicionário de mapeamentos por tipo
        """
        # Gera nomes falsos para pessoas
        for entity in entities.get('persons', []):
            original = entity.text
            if original not in self.mapping['persons']:
                # Tenta manter gênero baseado no nome
                self.mapping['persons'][original] = self.faker.name()
        
        # Gera CPFs falsos
        for entity in entities.get('cpfs', []):
            original = entity.text
            if original not in self.mapping['cpfs']:
                self.mapping['cpfs'][original] = generate_valid_cpf()
        
        # Gera RGs falsos
        for entity in entities.get('rgs', []):
            original = entity.text
            if original not in self.mapping['rgs']:
                self.mapping['rgs'][original] = generate_valid_rg()
        
        # Gera datas falsas (sempre antes de 2007 para garantir 18+ anos)
        for entity in entities.get('dates', []):
            original = entity.text
            if original not in self.mapping['dates']:
                self.mapping['dates'][original] = self._generate_adult_date(original)
        
        return self.mapping
    
    def _generate_adult_date(self, original_date: str) -> str:
        """
        Gera uma data de nascimento que resulte em pelo menos 18 anos em 2025.
        
        Args:
            original_date: Data original para manter o formato
        
        Returns:
            Data falsa no mesmo formato
        """
        # Detecta o formato da data
        if '/' in original_date:
            separator = '/'
            format_str = '%d/%m/%Y'
        elif '-' in original_date:
            separator = '-'
            format_str = '%d-%m-%Y'
        else:
            separator = '.'
            format_str = '%d.%m.%Y'
        
        # Gera data entre 1950 e 2006
        start_date = datetime(1950, 1, 1)
        end_date = datetime(2006, 12, 31)
        
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        fake_date = start_date + timedelta(days=random_days)
        
        return fake_date.strftime(format_str)
    
    def anonymize(self, text: str) -> Tuple[str, Dict[str, Dict[str, str]]]:
        """
        Anonimiza um texto, substituindo dados sensíveis.
        
        Args:
            text: Texto original
        
        Returns:
            Tupla (texto_anonimizado, mapeamento)
        """
        # Detecta entidades
        entities = self.detector.detect_all(text)
        
        # Gera substituições
        self.generate_replacements(entities)
        
        # Aplica substituições
        anonymized_text = text
        
        # Substitui na ordem: nomes (mais longos primeiro), CPFs, RGs, datas
        # Ordena nomes por tamanho (maiores primeiro) para evitar substituições parciais
        sorted_persons = sorted(
            self.mapping['persons'].items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        for original, replacement in sorted_persons:
            # Usa regex para substituir todas as ocorrências (case insensitive)
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            anonymized_text = pattern.sub(replacement, anonymized_text)
        
        # Substitui CPFs
        for original, replacement in self.mapping['cpfs'].items():
            anonymized_text = anonymized_text.replace(original, replacement)
        
        # Substitui RGs
        for original, replacement in self.mapping['rgs'].items():
            anonymized_text = anonymized_text.replace(original, replacement)
        
        # Substitui datas
        for original, replacement in self.mapping['dates'].items():
            anonymized_text = anonymized_text.replace(original, replacement)
        
        return anonymized_text, self.mapping
    
    def reverse(self, anonymized_text: str, mapping: Dict[str, Dict[str, str]]) -> str:
        """
        Reverte a anonimização usando o mapeamento.
        
        Args:
            anonymized_text: Texto anonimizado
            mapping: Mapeamento original -> falso
        
        Returns:
            Texto original restaurado
        """
        text = anonymized_text
        
        # Inverte o mapeamento (falso -> original)
        for entity_type, type_mapping in mapping.items():
            for original, replacement in type_mapping.items():
                if entity_type == 'persons':
                    pattern = re.compile(re.escape(replacement), re.IGNORECASE)
                    text = pattern.sub(original, text)
                else:
                    text = text.replace(replacement, original)
        
        return text
    
    def get_summary(self) -> Dict[str, int]:
        """
        Retorna resumo das substituições realizadas.
        
        Returns:
            Dicionário com contagem por tipo
        """
        return {
            'nomes': len(self.mapping['persons']),
            'cpfs': len(self.mapping['cpfs']),
            'rgs': len(self.mapping['rgs']),
            'datas': len(self.mapping['dates']),
        }


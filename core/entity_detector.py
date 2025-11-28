"""
Detector de entidades usando spaCy e regex.
Autor: Matheus C. Pestana

Detecta: nomes de pessoas, CPFs, RGs, datas de nascimento
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .validators import extract_cpfs, extract_rgs, extract_birth_dates


@dataclass
class DetectedEntity:
    """Representa uma entidade detectada no texto."""
    text: str
    entity_type: str  # 'PERSON', 'CPF', 'RG', 'DATE'
    start: int
    end: int
    extra: dict = field(default_factory=dict)


class EntityDetector:
    """Detector de entidades sensíveis em textos."""
    
    def __init__(self, spacy_model: str = "pt_core_news_lg"):
        """
        Inicializa o detector.
        
        Args:
            spacy_model: Nome do modelo spaCy a usar
        """
        self.spacy_model = spacy_model
        self._nlp = None
    
    @property
    def nlp(self):
        """Carrega o modelo spaCy sob demanda."""
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load(self.spacy_model)
            except OSError:
                raise RuntimeError(
                    f"Modelo spaCy '{self.spacy_model}' não encontrado. "
                    f"Instale com: python -m spacy download {self.spacy_model}"
                )
        return self._nlp
    
    def detect_all(self, text: str) -> Dict[str, List[DetectedEntity]]:
        """
        Detecta todas as entidades sensíveis no texto.
        
        Args:
            text: Texto para análise
        
        Returns:
            Dicionário com listas de entidades por tipo
        """
        return {
            'persons': self.detect_persons(text),
            'cpfs': self.detect_cpfs(text),
            'rgs': self.detect_rgs(text),
            'dates': self.detect_dates(text),
        }
    
    def detect_persons(self, text: str) -> List[DetectedEntity]:
        """
        Detecta nomes de pessoas usando spaCy.
        
        Args:
            text: Texto para análise
        
        Returns:
            Lista de entidades do tipo PERSON
        """
        doc = self.nlp(text)
        entities = []
        seen_texts = set()
        
        for ent in doc.ents:
            if ent.label_ == "PER":  # spaCy PT usa 'PER' para pessoas
                # Normaliza o nome para evitar duplicatas
                normalized = ent.text.strip()
                if normalized and normalized not in seen_texts:
                    seen_texts.add(normalized)
                    entities.append(DetectedEntity(
                        text=normalized,
                        entity_type='PERSON',
                        start=ent.start_char,
                        end=ent.end_char,
                    ))
        
        return entities
    
    def detect_cpfs(self, text: str) -> List[DetectedEntity]:
        """
        Detecta CPFs válidos no texto.
        
        Args:
            text: Texto para análise
        
        Returns:
            Lista de entidades do tipo CPF
        """
        cpfs = extract_cpfs(text)
        return [
            DetectedEntity(
                text=cpf,
                entity_type='CPF',
                start=start,
                end=end,
            )
            for cpf, start, end in cpfs
        ]
    
    def detect_rgs(self, text: str) -> List[DetectedEntity]:
        """
        Detecta RGs no texto.
        
        Args:
            text: Texto para análise
        
        Returns:
            Lista de entidades do tipo RG
        """
        rgs = extract_rgs(text)
        return [
            DetectedEntity(
                text=rg,
                entity_type='RG',
                start=start,
                end=end,
            )
            for rg, start, end in rgs
        ]
    
    def detect_dates(self, text: str) -> List[DetectedEntity]:
        """
        Detecta datas de nascimento no texto.
        
        Args:
            text: Texto para análise
        
        Returns:
            Lista de entidades do tipo DATE
        """
        dates = extract_birth_dates(text)
        return [
            DetectedEntity(
                text=date_str,
                entity_type='DATE',
                start=start,
                end=end,
                extra={'datetime': date_obj}
            )
            for date_str, start, end, date_obj in dates
        ]
    
    def get_unique_values(self, entities: Dict[str, List[DetectedEntity]]) -> Dict[str, Set[str]]:
        """
        Extrai valores únicos de cada tipo de entidade.
        
        Args:
            entities: Dicionário de entidades detectadas
        
        Returns:
            Dicionário com conjuntos de valores únicos por tipo
        """
        return {
            entity_type: {e.text for e in entity_list}
            for entity_type, entity_list in entities.items()
        }


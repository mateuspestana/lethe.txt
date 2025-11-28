#!/usr/bin/env python3
"""
Benchmark de bibliotecas de parsing de documentos.
Autor: Matheus C. Pestana

Testa python-docx, docx2txt e textract para escolher a melhor opção.
"""

import time
import tracemalloc
from pathlib import Path
from typing import Callable, Dict, Any
import sys

# Arquivos de teste
TEST_DIR = Path("test_files")
TEST_FILES = {
    "docx": TEST_DIR / "A Procuradoria.docx",
    "doc": TEST_DIR / "A Procuradoria.doc",
}


def measure_performance(func: Callable, filepath: Path, iterations: int = 5) -> Dict[str, Any]:
    """Mede tempo de execução e uso de memória de uma função."""
    times = []
    memory_peaks = []
    text_result = None
    error = None
    
    for i in range(iterations):
        tracemalloc.start()
        start = time.perf_counter()
        
        try:
            text_result = func(filepath)
        except Exception as e:
            error = str(e)
            tracemalloc.stop()
            break
            
        end = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        times.append(end - start)
        memory_peaks.append(peak)
    
    if error:
        return {"error": error}
    
    return {
        "avg_time_ms": sum(times) / len(times) * 1000,
        "min_time_ms": min(times) * 1000,
        "max_time_ms": max(times) * 1000,
        "avg_memory_kb": sum(memory_peaks) / len(memory_peaks) / 1024,
        "text_length": len(text_result) if text_result else 0,
        "text_preview": text_result[:200] if text_result else "",
    }


# Funções de parsing para cada biblioteca

def parse_with_python_docx(filepath: Path) -> str:
    """Extrai texto usando python-docx (apenas .docx)."""
    from docx import Document
    doc = Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])


def parse_with_docx2txt(filepath: Path) -> str:
    """Extrai texto usando docx2txt (apenas .docx)."""
    import docx2txt
    return docx2txt.process(str(filepath))


def parse_with_textract(filepath: Path) -> str:
    """Extrai texto usando textract (.doc, .docx, .pdf)."""
    import textract
    return textract.process(str(filepath)).decode("utf-8")


def run_benchmark():
    """Executa o benchmark completo."""
    print("=" * 70)
    print("BENCHMARK DE BIBLIOTECAS DE PARSING DE DOCUMENTOS")
    print("=" * 70)
    print()
    
    # Verificar arquivos de teste
    for file_type, filepath in TEST_FILES.items():
        if not filepath.exists():
            print(f"⚠️  Arquivo não encontrado: {filepath}")
    print()
    
    # Bibliotecas a testar
    parsers = {
        "python-docx": {"func": parse_with_python_docx, "formats": ["docx"]},
        "docx2txt": {"func": parse_with_docx2txt, "formats": ["docx"]},
        "textract": {"func": parse_with_textract, "formats": ["docx", "doc"]},
    }
    
    results = {}
    
    for parser_name, parser_info in parsers.items():
        print(f"\n{'─' * 70}")
        print(f"📦 Testando: {parser_name}")
        print(f"{'─' * 70}")
        
        results[parser_name] = {}
        
        for file_type in parser_info["formats"]:
            filepath = TEST_FILES.get(file_type)
            if not filepath or not filepath.exists():
                print(f"  [{file_type}] Arquivo não disponível")
                continue
            
            print(f"\n  📄 Arquivo: {filepath.name} ({file_type})")
            
            result = measure_performance(parser_info["func"], filepath)
            results[parser_name][file_type] = result
            
            if "error" in result:
                print(f"     ❌ Erro: {result['error']}")
            else:
                print(f"     ⏱️  Tempo médio: {result['avg_time_ms']:.2f}ms")
                print(f"     💾 Memória média: {result['avg_memory_kb']:.2f}KB")
                print(f"     📝 Caracteres extraídos: {result['text_length']}")
                print(f"     👀 Preview: {result['text_preview'][:100]}...")
    
    # Resumo comparativo
    print("\n" + "=" * 70)
    print("RESUMO COMPARATIVO")
    print("=" * 70)
    
    print("\n📊 Para arquivos .docx:")
    docx_results = []
    for parser_name, parser_results in results.items():
        if "docx" in parser_results and "error" not in parser_results["docx"]:
            r = parser_results["docx"]
            docx_results.append((parser_name, r["avg_time_ms"], r["avg_memory_kb"], r["text_length"]))
    
    if docx_results:
        docx_results.sort(key=lambda x: x[1])  # Ordenar por tempo
        print(f"{'Biblioteca':<15} {'Tempo (ms)':<12} {'Memória (KB)':<15} {'Caracteres'}")
        print("-" * 55)
        for name, time_ms, mem_kb, chars in docx_results:
            print(f"{name:<15} {time_ms:<12.2f} {mem_kb:<15.2f} {chars}")
        print(f"\n✅ Recomendação para .docx: {docx_results[0][0]} (mais rápido)")
    
    print("\n📊 Para arquivos .doc:")
    doc_results = []
    for parser_name, parser_results in results.items():
        if "doc" in parser_results and "error" not in parser_results["doc"]:
            r = parser_results["doc"]
            doc_results.append((parser_name, r["avg_time_ms"], r["avg_memory_kb"], r["text_length"]))
    
    if doc_results:
        doc_results.sort(key=lambda x: x[1])
        print(f"{'Biblioteca':<15} {'Tempo (ms)':<12} {'Memória (KB)':<15} {'Caracteres'}")
        print("-" * 55)
        for name, time_ms, mem_kb, chars in doc_results:
            print(f"{name:<15} {time_ms:<12.2f} {mem_kb:<15.2f} {chars}")
        print(f"\n✅ Recomendação para .doc: {doc_results[0][0]}")
    else:
        print("  Apenas textract suporta .doc (requer antiword instalado)")
    
    return results


if __name__ == "__main__":
    run_benchmark()


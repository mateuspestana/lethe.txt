#!/usr/bin/env python3
"""
Lethe.TXT - Anonimizador de Documentos
Interface CLI com Typer
Autor: Matheus C. Pestana
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from core.document_parser import extract_text, get_supported_extensions
from core.anonymizer import Anonymizer
from core.crypto import encrypt_mapping, decrypt_mapping, save_encrypted_mapping, load_encrypted_mapping

app = typer.Typer(
    name="lethe",
    help="🔒 Lethe.TXT - Anonimizador de Documentos",
    add_completion=False,
)
console = Console()


@app.command()
def anonymize(
    input_file: Path = typer.Argument(
        ...,
        help="Arquivo de entrada (txt, docx, doc, pdf)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Arquivo de saída (padrão: <input>_anonimizado.txt)",
    ),
    password: str = typer.Option(
        ...,
        "--password", "-p",
        prompt=True,
        hide_input=True,
        help="Senha para criptografar o mapeamento",
    ),
    mapping_output: Optional[Path] = typer.Option(
        None,
        "--mapping", "-m",
        help="Arquivo de mapeamento (padrão: <input>_mapping.lethe)",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed", "-s",
        help="Seed para resultados reproduzíveis",
    ),
    show_mapping: bool = typer.Option(
        False,
        "--show-mapping",
        help="Exibir mapeamento de substituições",
    ),
):
    """
    📝 Anonimiza um documento, substituindo dados sensíveis.
    
    Detecta e substitui: nomes, CPFs, RGs e datas de nascimento.
    """
    # Define arquivos de saída
    if output is None:
        output = input_file.parent / f"{input_file.stem}_anonimizado.txt"
    
    if mapping_output is None:
        mapping_output = input_file.parent / f"{input_file.stem}_mapping.lethe"
    
    console.print(Panel(
        f"[bold blue]Lethe.TXT[/bold blue] - Anonimizador de Documentos\n\n"
        f"📄 Entrada: [cyan]{input_file}[/cyan]\n"
        f"📤 Saída: [green]{output}[/green]\n"
        f"🔐 Mapeamento: [yellow]{mapping_output}[/yellow]",
        title="🔒 Processando",
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Extrai texto
        task = progress.add_task("Extraindo texto...", total=None)
        try:
            text_content = extract_text(input_file)
        except Exception as e:
            console.print(f"[red]❌ Erro ao extrair texto: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task, description="[green]✓ Texto extraído[/green]")
        
        # Anonimiza
        task2 = progress.add_task("Anonimizando...", total=None)
        try:
            anonymizer = Anonymizer(seed=seed)
            anonymized_text, mapping = anonymizer.anonymize(text_content)
        except Exception as e:
            console.print(f"[red]❌ Erro na anonimização: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task2, description="[green]✓ Anonimizado[/green]")
        
        # Salva arquivos
        task3 = progress.add_task("Salvando arquivos...", total=None)
        try:
            # Salva texto anonimizado
            output.write_text(anonymized_text, encoding='utf-8')
            
            # Salva mapeamento criptografado
            save_encrypted_mapping(mapping, password, str(mapping_output))
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task3, description="[green]✓ Arquivos salvos[/green]")
    
    # Exibe estatísticas
    summary = anonymizer.get_summary()
    
    table = Table(title="📊 Estatísticas de Anonimização")
    table.add_column("Tipo", style="cyan")
    table.add_column("Quantidade", justify="right", style="green")
    
    table.add_row("👤 Nomes", str(summary['nomes']))
    table.add_row("📋 CPFs", str(summary['cpfs']))
    table.add_row("🪪 RGs", str(summary['rgs']))
    table.add_row("📅 Datas", str(summary['datas']))
    
    console.print(table)
    
    # Exibe mapeamento se solicitado
    if show_mapping:
        console.print("\n[bold]🗺️ Mapeamento de Substituições:[/bold]")
        for entity_type, type_mapping in mapping.items():
            if type_mapping:
                console.print(f"\n[cyan]{entity_type.upper()}:[/cyan]")
                for original, replacement in type_mapping.items():
                    console.print(f"  [dim]{original}[/dim] → [green]{replacement}[/green]")
    
    console.print(f"\n[green]✅ Concluído![/green]")
    console.print(f"[yellow]💡 Guarde o arquivo de mapeamento e a senha para reverter![/yellow]")


@app.command()
def reverse(
    input_file: Path = typer.Argument(
        ...,
        help="Arquivo anonimizado",
        exists=True,
        readable=True,
    ),
    mapping_file: Path = typer.Argument(
        ...,
        help="Arquivo de mapeamento (.lethe)",
        exists=True,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Arquivo de saída (padrão: <input>_restaurado.txt)",
    ),
    password: str = typer.Option(
        ...,
        "--password", "-p",
        prompt=True,
        hide_input=True,
        help="Senha do mapeamento",
    ),
):
    """
    🔓 Reverte a anonimização usando o mapeamento criptografado.
    """
    # Define arquivo de saída
    if output is None:
        output = input_file.parent / f"{input_file.stem}_restaurado.txt"
    
    console.print(Panel(
        f"[bold blue]Lethe.TXT[/bold blue] - Reversão\n\n"
        f"📄 Texto anonimizado: [cyan]{input_file}[/cyan]\n"
        f"🔐 Mapeamento: [yellow]{mapping_file}[/yellow]\n"
        f"📤 Saída: [green]{output}[/green]",
        title="🔓 Revertendo",
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Carrega texto anonimizado
        task = progress.add_task("Carregando texto...", total=None)
        try:
            anon_text = input_file.read_text(encoding='utf-8')
        except Exception as e:
            console.print(f"[red]❌ Erro ao carregar texto: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task, description="[green]✓ Texto carregado[/green]")
        
        # Descriptografa mapeamento
        task2 = progress.add_task("Descriptografando mapeamento...", total=None)
        try:
            mapping = load_encrypted_mapping(str(mapping_file), password)
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]❌ Erro ao carregar mapeamento: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task2, description="[green]✓ Mapeamento descriptografado[/green]")
        
        # Reverte
        task3 = progress.add_task("Revertendo...", total=None)
        try:
            anonymizer = Anonymizer()
            original_text = anonymizer.reverse(anon_text, mapping)
        except Exception as e:
            console.print(f"[red]❌ Erro na reversão: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task3, description="[green]✓ Revertido[/green]")
        
        # Salva
        task4 = progress.add_task("Salvando...", total=None)
        try:
            output.write_text(original_text, encoding='utf-8')
        except Exception as e:
            console.print(f"[red]❌ Erro ao salvar: {e}[/red]")
            raise typer.Exit(1)
        progress.update(task4, description="[green]✓ Salvo[/green]")
    
    console.print(f"\n[green]✅ Documento restaurado em: {output}[/green]")


@app.command()
def info():
    """
    ℹ️ Exibe informações sobre o Lethe.TXT.
    """
    console.print(Panel(
        "[bold blue]Lethe.TXT[/bold blue]\n\n"
        "🔒 Anonimizador de Documentos\n\n"
        "[dim]Detecta e substitui dados sensíveis:[/dim]\n"
        "  • 👤 Nomes de pessoas (usando spaCy)\n"
        "  • 📋 CPFs (com validação)\n"
        "  • 🪪 RGs (com validação)\n"
        "  • 📅 Datas de nascimento\n\n"
        "[dim]Formatos suportados:[/dim]\n"
        f"  • {', '.join(get_supported_extensions()).upper()}\n\n"
        "[dim]Autor:[/dim] Matheus C. Pestana",
        title="ℹ️ Sobre",
    ))


if __name__ == "__main__":
    app()


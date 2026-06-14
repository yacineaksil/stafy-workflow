from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M"


def aujourd_hui():
    return datetime.now().strftime(DATE_FMT)


def maintenant():
    return datetime.now().strftime(DATETIME_FMT)


def saisir_float(label: str, defaut: float | None = None) -> float:
    while True:
        val = Prompt.ask(label, default=str(defaut) if defaut is not None else "")
        try:
            return float(val.replace(",", "."))
        except ValueError:
            console.print("[red]Valeur invalide, veuillez saisir un nombre.[/red]")


def saisir_int(label: str, defaut: int | None = None) -> int:
    while True:
        val = Prompt.ask(label, default=str(defaut) if defaut is not None else "")
        try:
            n = int(val)
            if n < 0:
                raise ValueError
            return n
        except ValueError:
            console.print("[red]Valeur invalide, veuillez saisir un entier positif.[/red]")


def saisir_date(label: str, defaut: str | None = None) -> str:
    defaut = defaut or aujourd_hui()
    while True:
        val = Prompt.ask(label, default=defaut)
        try:
            datetime.strptime(val, DATE_FMT)
            return val
        except ValueError:
            console.print(f"[red]Format attendu : AAAA-MM-JJ (ex: {aujourd_hui()})[/red]")


def choisir_parmi(options: list[str], label: str = "Choix") -> str:
    for i, opt in enumerate(options, 1):
        console.print(f"  [cyan]{i}[/cyan]. {opt}")
    while True:
        val = Prompt.ask(label)
        try:
            idx = int(val) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        console.print("[red]Choix invalide.[/red]")


def formater_montant(montant: float) -> str:
    return f"{montant:,.0f} FCFA".replace(",", " ")

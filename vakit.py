import requests
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

CITIES = {
    "sarajevo": {"lat": 43.8563, "lng": 18.4131},
    "banja luka": {"lat": 44.7722, "lng": 17.1910},
    "mostar": {"lat": 43.3438, "lng": 17.8078},
    "zenica": {"lat": 44.2038, "lng": 17.9084},
    "tuzla": {"lat": 44.5383, "lng": 18.6771},
}

PRAYER_TRANSLATIONS = {
    "Fajr": "Sabah",
    "Sunrise": "Izlazak sunca",
    "Dhuhr": "Podne",
    "Asr": "Ikindija",
    "Maghrib": "Akšam",
    "Isha": "Jacija"
}

def get_prayer_times(lat, lng):
    url = "http://api.aladhan.com/v1/timings"
    params = {
        "latitude": lat,
        "longitude": lng,
        "method": 2,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def get_next_prayer(timings):
    now = datetime.now()
    prayers_order = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    next_prayer = None
    next_time = None

    for prayer in prayers_order:
        time_str = timings[prayer]
        prayer_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        if prayer_time < now:
            prayer_time += timedelta(days=1)

        if next_time is None or prayer_time < next_time:
            next_time = prayer_time
            next_prayer = prayer

    return next_prayer, next_time

def format_countdown(tdelta):
    total_seconds = int(tdelta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def main():
    console.print("[bold green]Dobrodošli![/bold green] Unesite ime grada u Bosni za koji želite vakit:")
    city = console.input("Grad: ").strip().lower()

    if city not in CITIES:
        console.print(f"[red]Nažalost, nemamo podatke za grad '{city}'.[/red]")
        console.print("Molimo pokušajte sa Sarajevom, Banja Lukom, Mostarom, Zenicom ili Tuzlom.")
        return

    coords = CITIES[city]
    try:
        data = get_prayer_times(coords["lat"], coords["lng"])
    except requests.HTTPError as e:
        console.print(f"[red]Greška prilikom dohvaćanja podataka: {e}[/red]")
        return

    timings = data["data"]["timings"]
    date = data["data"]["date"]["gregorian"]["date"]

    prayer_names = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

    def build_table():
        table = Table(title=f"Vremena namaza za {city.title()} – {date}", style="bold cyan")
        table.add_column("Namaz", style="bold yellow")
        table.add_column("Vrijeme", style="bold magenta")
        for p in prayer_names:
            table.add_row(PRAYER_TRANSLATIONS.get(p, p), timings[p])
        return table

    next_prayer, next_time = get_next_prayer(timings)

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                now = datetime.now()
                remaining = next_time - now
                if remaining.total_seconds() <= 0:
                    data = get_prayer_times(coords["lat"], coords["lng"])
                    timings = data["data"]["timings"]
                    next_prayer, next_time = get_next_prayer(timings)

                countdown_str = format_countdown(remaining)

                panel = Panel.fit(
                    f"[bold green]Sljedeći namaz:[/bold green] {PRAYER_TRANSLATIONS.get(next_prayer, next_prayer)} u {next_time.strftime('%H:%M')}\n"
                    f"[bold red]Odbrojavanje:[/bold red] {countdown_str}",
                    title="Odbrojavanje do vakta",
                    border_style="bright_blue",
                )

                layout = Table.grid()
                layout.add_row(build_table())
                layout.add_row(panel)

                live.update(layout)
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Prekid programa. Doviđenja![/bold yellow]")

if __name__ == "__main__":
    main()

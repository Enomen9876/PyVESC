import tkinter as tk
from tkinter import messagebox
import threading
import time
from pyvesc import VESC

# --- KONFIGURACE ---
SERIAL_PORT = "COM18"
POLE_PAIRS = 7        # Počet párů pólů vašeho motoru
WHEEL_DIAMETER = 0.1  # Průměr kola v metrech (např. 10cm)
GEAR_RATIO = 1.0      # Převodový poměr (1.0 = přímý náhon)

class VescControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VESC Control Panel")
        self.vesc = None
        self.running = False

        # --- UI PRVKY ---
        # Vstup pro RPM
        tk.Label(root, text="Cílové RPM:").grid(row=0, column=0, padx=10, pady=10)
        self.rpm_entry = tk.Entry(root)
        self.rpm_entry.insert(0, "1000")
        self.rpm_entry.grid(row=0, column=1, padx=10, pady=10)

        # Tlačítka
        self.start_btn = tk.Button(root, text="START", command=self.start_motor, bg="green", fg="white", width=10)
        self.start_btn.grid(row=1, column=0, padx=10, pady=10)

        self.stop_btn = tk.Button(root, text="STOP (Brzda)", command=self.stop_motor, bg="red", fg="white", width=10)
        self.stop_btn.grid(row=1, column=1, padx=10, pady=10)

        # Displej pro data
        self.status_label = tk.Label(root, text="Stav: Odpojeno", font=("Arial", 10, "bold"))
        self.status_label.grid(row=2, column=0, columnspan=2, pady=5)

        self.data_label = tk.Label(root, text="RPM: 0\nVzdálenost: 0.00 m\nNapětí: 0.0 V", font=("Courier", 12), justify="left")
        self.data_label.grid(row=3, column=0, columnspan=2, padx=10, pady=20)

        # Inicializace VESC v samostatném vlákně
        self.connect_vesc()

    def connect_vesc(self):
        try:
            self.vesc = VESC(serial_port=SERIAL_PORT, baudrate=115200)
            self.status_label.config(text=f"Stav: Připojeno ({SERIAL_PORT})", fg="blue")
            self.running = True
            # Spuštění smyčky pro čtení dat
            threading.Thread(target=self.update_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Chyba připojení", f"Nepodařilo se připojit k VESC: {e}")

    def update_loop(self):
        """Smyčka pro pravidelné čtení dat z VESC."""
        while self.running:
            if self.vesc:
                data = self.vesc.get_measurements()
                if data:
                    rpm = getattr(data, 'rpm', 0)
                    tacho = getattr(data, 'tachometer', 0)
                    voltage = getattr(data, 'v_in', 0)

                    # Výpočet vzdálenosti
                    # Tachometr u VESC počítá ERPM kroky. Musíme vydělit póly motoru.
                    wheel_circ = WHEEL_DIAMETER * 3.14159
                    distance = (tacho / (POLE_PAIRS * GEAR_RATIO)) * wheel_circ

                    # Aktualizace UI
                    display_text = (
                        f"RPM:          {rpm:>8}\n"
                        f"Vzdálenost:   {distance:>8.2f} m\n"
                        f"Napětí:       {voltage:>8.1f} V"
                    )
                    self.data_label.config(text=display_text)
            
            time.sleep(0.1) # Obnovovací frekvence 10Hz

    def start_motor(self):
        try:
            target_rpm = int(self.rpm_entry.get())
            if self.vesc:
                self.vesc.set_rpm(target_rpm)
        except ValueError:
            messagebox.showwarning("Chyba", "Zadejte platné číslo pro RPM")

    def stop_motor(self):
        if self.vesc:
            # Nastavení RPM na 0 zastaví motor aktivně
            self.vesc.set_rpm(0)
            # Případně set_current(0) pro volnoběh
            # self.vesc.set_current(0)

    def on_closing(self):
        self.running = False
        if self.vesc:
            self.vesc.set_rpm(0)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VescControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
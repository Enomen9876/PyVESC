import tkinter as tk
from tkinter import messagebox
import threading
import time
from controller.odometry import VescControll
from controller.controll import SafetyController, MotorController
from controller.config import *

class VescApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VESC Odometrie & Ovládání")
        self.root.geometry("360x500")

        self.odo = VescControll()
        self.safety = SafetyController(max_speed_m_s=MAX_SPEED)
        self.motor = MotorController(self.odo, self.safety)
        self.is_running = False
        self.last_command = "stopped"

        # --- UI PRVKY ---
        tk.Label(root, text="Cílové RPM (VESC same):").pack(pady=4)
        self.rpm_input = tk.Entry(root, justify="center")
        self.rpm_input.insert(0, "500")
        self.rpm_input.pack(pady=4)

        tk.Button(root, text="Nastavit RPM", command=self.handle_start_rpm, width=24).pack(pady=4)

        tk.Label(root, text="Cílová rychlost (m/s):").pack(pady=4)
        self.speed_input = tk.Entry(root, justify="center")
        self.speed_input.insert(0, "0.5")
        self.speed_input.pack(pady=4)

        tk.Button(root, text="Nastavit rychlost", command=self.handle_start_speed, width=24).pack(pady=4)

        tk.Label(root, text="Nastavit vzdálenost (m):").pack(pady=4)
        self.distance_input = tk.Entry(root, justify="center")
        self.distance_input.insert(0, "0.0")
        self.distance_input.pack(pady=4)

        tk.Button(root, text="Set vzdálenost", command=self.handle_set_distance, width=24).pack(pady=4)
        tk.Button(root, text="Reset vzdálenosti", command=self.handle_reset_distance, width=24).pack(pady=4)

        self.btn_stop = tk.Button(root, text="STOP / BRZDA", bg="red", fg="white", command=self.handle_stop, width=24)
        self.btn_stop.pack(pady=6)

        tk.Frame(root, height=2, bd=1, relief="sunken").pack(fill="x", padx=10, pady=10)

        self.lbl_stats = tk.Label(root, text="Čekám na data...", font=("Courier", 10), justify="left", anchor="w")
        self.lbl_stats.pack(padx=8, pady=8, fill="x")

        self.lbl_safety = tk.Label(root, text=f"Max rychlost (bezpečí): {self.safety.max_speed_m_s:.2f} m/s", fg="blue")
        self.lbl_safety.pack(pady=2)

        if self.odo.connect():
            self.is_running = True
            threading.Thread(target=self.update_loop, daemon=True).start()
        else:
            messagebox.showerror("Chyba", "Nepodařilo se připojit k VESC!")

    def update_loop(self):
        while self.is_running:
            try:
                data = self.motor.read_raw_data()
                if data:
                        txt = (
                            f"Motor rpm:  {data['motor_rpm']:.1f} RPM\n"
                            f"Wheel rpm:  {data['wheel_rpm']:.2f} RPM\n"
                            f"Rychlost:   {data['speed_m_s']:.3f} m/s\n"
                            f"Vzdálenost: {data['distance_m']:.3f} m\n"
                            f"Napětí:     {data['voltage']:.2f} V\n"
                            f"Tacho raw:  {data['tacho']:.1f} \n"
                            f"Poslední příkaz: {self.last_command}"
                        )
                        if self.root.winfo_exists():
                            self.root.after(0, self.update_ui_text, txt)
                else:
                    # Pokud data nepřišla, nekonči smyčku, jen počkej
                    print("Data z VESC jsou dočasně nedostupná...")
            except Exception as e:
                print(f"Update loop error: {e}")
                # Místo break zkusíme krátce počkat
                time.sleep(1) 
        
            time.sleep(0.1) # Frekvence obnovování 10Hz

    def update_ui_text(self, txt):
        try:
            if self.root.winfo_exists():
                self.lbl_stats.config(text=txt)
        except Exception:
            pass

    def handle_start_rpm(self):
        try:
            rpm = float(self.rpm_input.get())
            raw_rpm = self.motor.set_speed_rpm(rpm)
            self.last_command = f"rpm {rpm:.2f} (raw {raw_rpm:.0f})"
        except ValueError:
            messagebox.showwarning("Vstup", "Zadejte platné číslo pro RPM!")

    def handle_start_speed(self):
        try:
            speed = float(self.speed_input.get())
            raw_rpm = self.motor.set_speed_m_s(speed)
            self.last_command = f"speed {speed:.3f} m/s (raw {raw_rpm:.0f})"
            if abs(speed) > self.safety.max_speed_m_s:
                messagebox.showwarning("Safety", f"Max speed is {self.safety.max_speed_m_s:.2f} m/s momentálně clamped.")
        except ValueError:
            messagebox.showwarning("Vstup", "Zadejte platné číslo pro rychlost!")

    def handle_set_distance(self):
        try:
            dist = float(self.distance_input.get())
            self.motor.set_distance(dist)
            self.last_command = f"set distance {dist:.3f} m"
        except ValueError:
            messagebox.showwarning("Vstup", "Zadejte platné číslo pro vzdálenost!")

    def handle_reset_distance(self):
        self.motor.reset_distance()
        self.last_command = "reset distance"

    def handle_stop(self):
        self.motor.stop()
        self.last_command = "stop"

    def on_close(self):
        self.is_running = False
        time.sleep(0.2)
        if hasattr(self, 'motor') and self.motor and hasattr(self.motor, 'stop'):
            self.motor.stop()
        if hasattr(self, 'odo') and self.odo:
            self.odo.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VescApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
    
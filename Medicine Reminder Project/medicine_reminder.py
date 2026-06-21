# ============================================================
#  MediMind - Medicine Reminder App
#  Python Midterm Project
#  Uses: tkinter (built-in), threading, datetime
#  Install plyer for desktop notifications:
#      pip install plyer
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
from datetime import datetime, timedelta

# Optional: desktop notifications (install with: pip install plyer)
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
#  Colour Palette
# ─────────────────────────────────────────────────────────────
BG_MAIN      = "#f0f4f8"
BG_CARD      = "#ffffff"
BG_HEADER    = "#1a73e8"
COLOR_GREEN  = "#27ae60"
COLOR_RED    = "#e74c3c"
COLOR_ORANGE = "#f39c12"
COLOR_BLUE   = "#1a73e8"
COLOR_DARK   = "#2c3e50"
COLOR_LIGHT  = "#ecf0f1"
COLOR_GRAY   = "#95a5a6"
FG_WHITE     = "#ffffff"

FONT_TITLE   = ("Segoe UI", 20, "bold")
FONT_HEADING = ("Segoe UI", 12, "bold")
FONT_NORMAL  = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_CLOCK   = ("Segoe UI", 13, "bold")


class MedicineReminderApp:
    """Main application class for MediMind."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MediMind – Medicine Reminder")
        self.root.geometry("720x580")
        self.root.minsize(680, 520)
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(True, True)

        # ── App State ──────────────────────────────────────────
        self.medicines: list[dict] = []
        self.running = True
        self._next_id = 0          # auto-increment ID for each medicine

        # ── Build UI ───────────────────────────────────────────
        self._configure_styles()
        self._build_header()
        self._build_input_card()
        self._build_table_card()
        self._build_status_bar()

        # ── Background reminder thread ─────────────────────────
        t = threading.Thread(target=self._reminder_loop, daemon=True)
        t.start()

        # ── Live clock update ──────────────────────────────────
        self._tick_clock()

    # ─────────────────────────────────────────────────────────
    #  Style Configuration
    # ─────────────────────────────────────────────────────────
    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame",         background=BG_MAIN)
        style.configure("Card.TFrame",    background=BG_CARD,   relief="flat")
        style.configure("TLabel",         background=BG_MAIN,   font=FONT_NORMAL, foreground=COLOR_DARK)
        style.configure("Card.TLabel",    background=BG_CARD,   font=FONT_NORMAL, foreground=COLOR_DARK)
        style.configure("Heading.TLabel", background=BG_CARD,   font=FONT_HEADING, foreground=COLOR_DARK)

        # Primary button (blue)
        style.configure("Primary.TButton",
                         font=FONT_HEADING, foreground=FG_WHITE,
                         background=COLOR_BLUE, borderwidth=0, padding=(12, 6))
        style.map("Primary.TButton",
                  background=[("active", "#1558b0"), ("pressed", "#0d47a1")])

        # Danger button (red)
        style.configure("Danger.TButton",
                         font=FONT_NORMAL, foreground=FG_WHITE,
                         background=COLOR_RED, borderwidth=0, padding=(10, 5))
        style.map("Danger.TButton",
                  background=[("active", "#c0392b"), ("pressed", "#a93226")])

        # Test button (orange)
        style.configure("Test.TButton",
                         font=FONT_NORMAL, foreground=FG_WHITE,
                         background=COLOR_ORANGE, borderwidth=0, padding=(10, 5))
        style.map("Test.TButton",
                  background=[("active", "#d68910"), ("pressed", "#b7770d")])

        # Entry
        style.configure("TEntry", fieldbackground=BG_CARD, font=FONT_NORMAL,
                         foreground=COLOR_DARK, borderwidth=1)

        # Treeview
        style.configure("Treeview",
                         background=BG_CARD, fieldbackground=BG_CARD,
                         font=FONT_NORMAL, foreground=COLOR_DARK,
                         rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading",
                         font=FONT_HEADING, background=COLOR_LIGHT,
                         foreground=COLOR_DARK, relief="flat")
        style.map("Treeview",
                  background=[("selected", "#d0e4ff")],
                  foreground=[("selected", COLOR_DARK)])

    # ─────────────────────────────────────────────────────────
    #  Header Bar
    # ─────────────────────────────────────────────────────────
    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text="💊  MediMind", font=FONT_TITLE,
                 bg=BG_HEADER, fg=FG_WHITE).pack(side=tk.LEFT, padx=20, pady=12)

        tk.Label(header, text="Your Personal Medicine Reminder", font=FONT_SMALL,
                 bg=BG_HEADER, fg="#c8d8f8").pack(side=tk.LEFT, padx=0, pady=12)

        # Live clock on the right
        self.clock_var = tk.StringVar(value="--:--:--")
        tk.Label(header, textvariable=self.clock_var, font=FONT_CLOCK,
                 bg=BG_HEADER, fg=FG_WHITE).pack(side=tk.RIGHT, padx=20)

    # ─────────────────────────────────────────────────────────
    #  Input Card
    # ─────────────────────────────────────────────────────────
    def _build_input_card(self):
        card = tk.Frame(self.root, bg=BG_CARD, bd=0, relief="flat")
        card.pack(fill=tk.X, padx=20, pady=(14, 6))

        # Card shadow effect via a slightly darker outer frame
        tk.Label(card, text="Add a New Medicine", font=FONT_HEADING,
                 bg=BG_CARD, fg=COLOR_DARK).grid(row=0, column=0, columnspan=6,
                                                  sticky=tk.W, padx=16, pady=(12, 6))

        # ── Row 1: inputs ──────────────────────────────────────
        tk.Label(card, text="Medicine Name:", bg=BG_CARD, font=FONT_NORMAL,
                 fg=COLOR_DARK).grid(row=1, column=0, padx=(16, 4), pady=8, sticky=tk.W)

        self.med_name_var = tk.StringVar()
        name_entry = tk.Entry(card, textvariable=self.med_name_var, width=22,
                              font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_DARK,
                              relief="flat", bd=4, insertbackground=COLOR_DARK)
        name_entry.grid(row=1, column=1, padx=4, pady=8)
        name_entry.bind("<Return>", lambda e: self._add_medicine())

        tk.Label(card, text="Dosage (optional):", bg=BG_CARD, font=FONT_NORMAL,
                 fg=COLOR_DARK).grid(row=1, column=2, padx=(12, 4), pady=8, sticky=tk.W)

        self.med_dose_var = tk.StringVar()
        dose_entry = tk.Entry(card, textvariable=self.med_dose_var, width=12,
                              font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_DARK,
                              relief="flat", bd=4, insertbackground=COLOR_DARK)
        dose_entry.grid(row=1, column=3, padx=4, pady=8)

        tk.Label(card, text="Time (HH:MM):", bg=BG_CARD, font=FONT_NORMAL,
                 fg=COLOR_DARK).grid(row=1, column=4, padx=(12, 4), pady=8, sticky=tk.W)

        self.med_time_var = tk.StringVar()
        time_entry = tk.Entry(card, textvariable=self.med_time_var, width=8,
                              font=FONT_NORMAL, bg=COLOR_LIGHT, fg=COLOR_DARK,
                              relief="flat", bd=4, insertbackground=COLOR_DARK)
        time_entry.grid(row=1, column=5, padx=4, pady=8)
        time_entry.bind("<Return>", lambda e: self._add_medicine())

        # ── Row 2: buttons ─────────────────────────────────────
        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.grid(row=2, column=0, columnspan=6, sticky=tk.W, padx=12, pady=(0, 12))

        ttk.Button(btn_frame, text="➕  Add Medicine",
                   style="Primary.TButton", command=self._add_medicine).pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_frame, text="🗑  Remove Selected",
                   style="Danger.TButton", command=self._remove_medicine).pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_frame, text="⚡  Test Reminder Now",
                   style="Test.TButton", command=self._test_reminder).pack(side=tk.LEFT, padx=4)

        # Hint label
        tk.Label(btn_frame, text="  Tip: Use 24-hour format, e.g. 08:00 or 14:30",
                 bg=BG_CARD, fg=COLOR_GRAY, font=FONT_SMALL).pack(side=tk.LEFT, padx=8)

    # ─────────────────────────────────────────────────────────
    #  Table Card
    # ─────────────────────────────────────────────────────────
    def _build_table_card(self):
        card = tk.Frame(self.root, bg=BG_CARD)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)

        tk.Label(card, text="Today's Medicine Schedule", font=FONT_HEADING,
                 bg=BG_CARD, fg=COLOR_DARK).pack(anchor=tk.W, padx=16, pady=(12, 6))

        table_frame = tk.Frame(card, bg=BG_CARD)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        columns = ("name", "dosage", "time", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", selectmode="browse")

        self.tree.heading("name",   text="Medicine Name")
        self.tree.heading("dosage", text="Dosage")
        self.tree.heading("time",   text="Scheduled Time")
        self.tree.heading("status", text="Status")

        self.tree.column("name",   width=200, anchor=tk.W)
        self.tree.column("dosage", width=120, anchor=tk.CENTER)
        self.tree.column("time",   width=130, anchor=tk.CENTER)
        self.tree.column("status", width=180, anchor=tk.CENTER)

        # Row colour tags
        self.tree.tag_configure("pending",  background="#fef9e7")
        self.tree.tag_configure("taken",    background="#eafaf1", foreground=COLOR_GREEN)
        self.tree.tag_configure("missed",   background="#fdecea", foreground=COLOR_RED)
        self.tree.tag_configure("upcoming", background="#eaf4fb")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ─────────────────────────────────────────────────────────
    #  Status Bar
    # ─────────────────────────────────────────────────────────
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=COLOR_LIGHT, height=28)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready – Add your medicines above to get started.")
        tk.Label(bar, textvariable=self.status_var, bg=COLOR_LIGHT,
                 fg=COLOR_GRAY, font=FONT_SMALL, anchor=tk.W).pack(side=tk.LEFT, padx=12)

        self.count_var = tk.StringVar(value="Medicines: 0")
        tk.Label(bar, textvariable=self.count_var, bg=COLOR_LIGHT,
                 fg=COLOR_GRAY, font=FONT_SMALL).pack(side=tk.RIGHT, padx=12)

    # ─────────────────────────────────────────────────────────
    #  Live Clock
    # ─────────────────────────────────────────────────────────
    def _tick_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ─────────────────────────────────────────────────────────
    #  Add Medicine
    # ─────────────────────────────────────────────────────────
    def _add_medicine(self):
        name     = self.med_name_var.get().strip()
        dosage   = self.med_dose_var.get().strip() or "As prescribed"
        time_str = self.med_time_var.get().strip()

        if not name:
            messagebox.showwarning("Missing Name", "Please enter the medicine name.")
            return
        if not time_str:
            messagebox.showwarning("Missing Time", "Please enter the scheduled time.")
            return

        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time",
                                 "Time must be in HH:MM format.\n"
                                 "Examples: 08:00  |  13:30  |  22:00")
            return

        med_id = self._next_id
        self._next_id += 1

        med = {
            "id":             med_id,
            "name":           name,
            "dosage":         dosage,
            "time":           time_str,
            "taken":          False,
            "notified":       False,
            "missed_asked":   False,
            "follow_up_time": None,
        }
        self.medicines.append(med)

        self.tree.insert("", tk.END, iid=str(med_id),
                         values=(name, dosage, time_str, "⏳ Pending"),
                         tags=("pending",))

        self.med_name_var.set("")
        self.med_dose_var.set("")
        self.med_time_var.set("")
        self._update_count()
        self._set_status(f"✅  '{name}' added – reminder set for {time_str}.")

    # ─────────────────────────────────────────────────────────
    #  Remove Medicine
    # ─────────────────────────────────────────────────────────
    def _remove_medicine(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nothing Selected", "Please click a medicine row to select it first.")
            return

        med_id = int(selected[0])
        med    = self._find_med(med_id)
        name   = med["name"] if med else "medicine"

        confirm = messagebox.askyesno("Confirm Remove",
                                      f"Remove '{name}' from your schedule?")
        if confirm:
            self.medicines = [m for m in self.medicines if m["id"] != med_id]
            self.tree.delete(selected[0])
            self._update_count()
            self._set_status(f"🗑  '{name}' removed from schedule.")

    # ─────────────────────────────────────────────────────────
    #  Test Reminder (fires immediately for the selected row)
    # ─────────────────────────────────────────────────────────
    def _test_reminder(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Nothing Selected",
                                "Select a medicine row first, then click Test Reminder.")
            return
        med_id = int(selected[0])
        med    = self._find_med(med_id)
        if med:
            self._fire_reminder(med, test=True)

    # ─────────────────────────────────────────────────────────
    #  Reminder Loop (background thread)
    # ─────────────────────────────────────────────────────────
    def _reminder_loop(self):
        while self.running:
            now          = datetime.now()
            current_hhmm = now.strftime("%H:%M")

            for med in list(self.medicines):
                # ── Initial reminder ──────────────────────────
                if (current_hhmm == med["time"]
                        and not med["taken"]
                        and not med["notified"]):
                    med["notified"]       = True
                    follow_up             = now + timedelta(minutes=30)
                    med["follow_up_time"] = follow_up.strftime("%H:%M")
                    self._fire_reminder(med)

                # ── 30-minute follow-up ───────────────────────
                if (med["follow_up_time"]
                        and current_hhmm == med["follow_up_time"]
                        and not med["taken"]
                        and not med["missed_asked"]):
                    med["missed_asked"] = True
                    self.root.after(0, lambda m=med: self._ask_if_taken(m))

                # ── Midnight reset ────────────────────────────
                if current_hhmm == "00:00":
                    med["taken"]        = False
                    med["notified"]     = False
                    med["missed_asked"] = False
                    med["follow_up_time"] = None
                    self.root.after(0, lambda m=med: self._update_row(m, "⏳ Pending", "pending"))

            time.sleep(30)   # poll every 30 seconds

    # ─────────────────────────────────────────────────────────
    #  Fire Reminder Notification
    # ─────────────────────────────────────────────────────────
    def _fire_reminder(self, med: dict, test: bool = False):
        title   = "💊 Time for Your Medicine!" if not test else "💊 Test Reminder"
        message = (f"Please take  {med['name']}\n"
                   f"Dosage: {med['dosage']}\n"
                   f"Scheduled: {med['time']}")

        # Desktop notification (if plyer is installed)
        if PLYER_AVAILABLE:
            try:
                notification.notify(title=title, message=message,
                                    app_name="MediMind", timeout=10)
            except Exception:
                pass

        # In-app popup (always shown)
        self.root.after(0, lambda: messagebox.showinfo(title, message))
        self._set_status(f"🔔  Reminder sent for '{med['name']}' at {med['time']}.")

    # ─────────────────────────────────────────────────────────
    #  Ask If Medicine Was Taken (30-min follow-up)
    # ─────────────────────────────────────────────────────────
    def _ask_if_taken(self, med: dict):
        taken = messagebox.askyesno(
            "Did You Take Your Medicine?",
            f"It has been 30 minutes since your scheduled dose.\n\n"
            f"Medicine : {med['name']}\n"
            f"Dosage   : {med['dosage']}\n"
            f"Time     : {med['time']}\n\n"
            f"Did you take it?"
        )

        if taken:
            med["taken"] = True
            self._update_row(med, "✅ Taken", "taken")
            self._set_status(f"✅  Great! '{med['name']}' marked as taken.")
            messagebox.showinfo("Well Done! 🎉",
                                f"Great job taking your {med['name']}!\n"
                                f"Stay healthy and keep up the good work.")
        else:
            self._update_row(med, "❌ Missed – Take Now!", "missed")
            self._set_status(f"⚠️  '{med['name']}' was missed. Please take it now!")

            # Find the next upcoming medicine to remind about
            next_med = self._get_next_medicine(med)
            extra    = ""
            if next_med:
                extra = (f"\n\nAlso remember: your next medicine is\n"
                         f"'{next_med['name']}' at {next_med['time']}.")

            messagebox.showwarning(
                "Missed Medicine – Please Take Now!",
                f"You missed your {med['name']} ({med['dosage']}).\n"
                f"Please take it as soon as possible!{extra}"
            )

    # ─────────────────────────────────────────────────────────
    #  Helper: Get Next Upcoming Medicine
    # ─────────────────────────────────────────────────────────
    def _get_next_medicine(self, current_med: dict) -> dict | None:
        now_str = datetime.now().strftime("%H:%M")
        upcoming = [
            m for m in self.medicines
            if m["id"] != current_med["id"]
            and not m["taken"]
            and m["time"] > now_str
        ]
        if not upcoming:
            return None
        return min(upcoming, key=lambda m: m["time"])

    # ─────────────────────────────────────────────────────────
    #  Helper: Update a Treeview Row
    # ─────────────────────────────────────────────────────────
    def _update_row(self, med: dict, status_text: str, tag: str):
        try:
            self.tree.item(str(med["id"]),
                           values=(med["name"], med["dosage"], med["time"], status_text),
                           tags=(tag,))
        except tk.TclError:
            pass   # row may have been deleted

    # ─────────────────────────────────────────────────────────
    #  Helper: Find Medicine by ID
    # ─────────────────────────────────────────────────────────
    def _find_med(self, med_id: int) -> dict | None:
        for m in self.medicines:
            if m["id"] == med_id:
                return m
        return None

    # ─────────────────────────────────────────────────────────
    #  Helper: Update Status Bar
    # ─────────────────────────────────────────────────────────
    def _set_status(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def _update_count(self):
        n = len(self.medicines)
        self.count_var.set(f"Medicines: {n}")

    # ─────────────────────────────────────────────────────────
    #  Clean Shutdown
    # ─────────────────────────────────────────────────────────
    def on_closing(self):
        if messagebox.askokcancel("Quit MediMind",
                                  "Are you sure you want to close MediMind?\n"
                                  "All reminders will stop."):
            self.running = False
            self.root.destroy()


# ─────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = MedicineReminderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

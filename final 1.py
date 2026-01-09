import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import random
from datetime import datetime

# Optional PIL flag (not used in this layout fix)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

# WhatsApp (PyWhatKit)
try:
    import pywhatkit as kit
    try:
        import requests
        requests.get("https://google.com", timeout=80)
    except Exception:
        print("Internet check failed, disabling WhatsApp features")
        kit = None
except Exception as e:
    print("PyWhatKit import failed:", e)
    kit = None


# ==================== Database Connection ====================
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="puppy",
        database="bank_db"
    )


# ==================== Utility Functions =====================
def generate_acc_no():
    while True:
        acc_no = f"BNK{random.randint(10000, 99999)}"
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("SELECT COUNT(*) FROM accounts WHERE account_no=%s", (acc_no,))
            exists = cur.fetchone()[0] > 0
            db.close()
            if not exists:
                return acc_no
        except:
            return acc_no


def generate_ifsc():
    return f"IFSC{random.randint(1000, 9999)}"


def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_positive_amount(text):
    try:
        val = float(text)
        return val > 0
    except:
        return False


def sanitize_amount(text):
    return f"{float(text):.2f}"


def is_valid_mobile(m):
    return m.isdigit() and len(m) == 10


def build_whatsapp_summary(account_no):
    try:
        db = connect_db()
        cur = db.cursor()
        cur.execute("""
            SELECT a.balance, a.cust_name, c.mobile
            FROM accounts a
            JOIN customers c ON a.cust_id=c.cust_id
            WHERE a.account_no=%s
        """, (account_no,))
        row = cur.fetchone()
        if not row:
            db.close()
            return None, None, "Account not found"
        balance, cust_name, mobile = row

        cur.execute("""
            SELECT txn_type, amount, txn_date
            FROM transactions
            WHERE account_no=%s
            ORDER BY txn_date DESC, txn_id DESC
            LIMIT 5
        """, (account_no,))
        txns = cur.fetchall()
        db.close()

        lines = [
            "Bank Summary",
            f"Account: {account_no}",
            f"Name: {cust_name}",
            f"Balance: ₹{balance}",
            "Recent transactions:"
        ]
        if txns:
            for t_type, amt, t_date in txns:
                lines.append(f"- {t_type}: ₹{amt} on {t_date}")

        msg = "\n".join(lines)
        return mobile, msg, None
    except Exception as e:
        return None, None, str(e)


def send_whatsapp_message(mobile, message):
    if kit is None:
        return "PyWhatKit not installed or internet unavailable. Run: pip install pywhatkit"
    if not is_valid_mobile(mobile):
        return "Invalid mobile in database (must be 10 digits)."
    try:
        phone = f"+91{mobile}"
        kit.sendwhatmsg_instantly(
            phone_no=phone,
            message=message,
            wait_time=40,
            tab_close=True,
            close_time=10
        )
        return None
    except Exception as e:
        return str(e)


# ==================== Main App Class ========================
class BankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏦 BANK MANAGEMENT SYSTEM")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        # Theme
        self.colors = {
            "bg": "#0b1021",
            "panel": "#101a2b",
            "accent": "#1fb6ff",       # Not used for dashboards per request
            "danger": "#ff4d4d",
            "text_primary": "#eaf2ff",
            "text_muted": "#94a3b8",
            "border": "#16233b",
            "ring1": "#123a57",
            "ring2": "#155e85",
            "ring3": "#1b84b1",
            "ring4": "#20c4ff",
        }
        self._build_styles()

        # State
        self.emp_name = None
        self.cust_name = None
        self.cust_acc_no = None

        # Frames
        pages = [
            "main","emp_login","cust_login",
            "emp_dash","cust_dash",
            "add_cust","create_acc",
            "deposit","withdraw","block","transactions","transfer","pin_change",
            "cust_deposit","cust_withdraw","cust_transactions","cust_balance"
        ]
        self.frames = {}
        self.left_canvases = {}
        self.right_panels = {}
        self.titles = {}

        for name in pages:
            frame = tk.Frame(root, bg=self.colors["bg"])
            frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.frames[name] = frame
            self._scaffold_page(name, title="")

        # Build pages
        self.create_main()
        self.create_emp_login()
        self.create_cust_login()
        self.create_emp_dashboard()
        self.create_cust_dashboard()
        self.create_add_customer()
        self.create_create_account()
        self.create_deposit()
        self.create_withdraw()
        self.create_block_account()
        self.create_transactions()
        self.create_transfer()
        self.create_pin_change()
        self.create_cust_deposit()
        self.create_cust_withdraw()
        self.create_cust_transactions()  # full-width, scrollable per request
        self.create_cust_balance()

        self.show_frame("main")

    # -------------------- Styles --------------------
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Neutral panel-style for dashboard buttons
        style.configure("Secondary.TButton",
                        font=("Segoe UI", 12, "bold"),
                        padding=10,
                        foreground=self.colors["text_primary"],
                        background=self.colors["panel"],
                        bordercolor=self.colors["border"])
        style.map("Secondary.TButton",
                  background=[("active", "#16233b")],
                  bordercolor=[("active", "#16233b")])

        style.configure("Danger.TButton",
                        font=("Segoe UI", 12, "bold"),
                        padding=10,
                        foreground="#ffffff",
                        background=self.colors["danger"],
                        bordercolor=self.colors["danger"])
        style.map("Danger.TButton",
                  background=[("active", "#ff6666")],
                  bordercolor=[("active", "#ff6666")])

        style.configure("Dark.TEntry",
                        fieldbackground=self.colors["panel"],
                        foreground=self.colors["text_primary"],
                        bordercolor=self.colors["border"],
                        padding=6)

        style.configure("Dark.TCombobox",
                        fieldbackground=self.colors["panel"],
                        foreground=self.colors["text_primary"],
                        bordercolor=self.colors["border"],
                        padding=6)

        style.configure("Dark.Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["text_primary"],
                        fieldbackground=self.colors["panel"],
                        bordercolor=self.colors["border"],
                        rowheight=28)

        style.configure("Dark.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#0f1629",
                        foreground=self.colors["text_primary"],
                        bordercolor=self.colors["border"])

    # -------------------- Page scaffold --------------------
    def _scaffold_page(self, name, title=""):
        frame = self.frames[name]
        # Left hero canvas
        left = tk.Canvas(frame, bg=self.colors["bg"], highlightthickness=0)
        left.place(relx=0, rely=0, relwidth=0.55, relheight=1)
        self.left_canvases[name] = left
        frame.bind("<Configure>", lambda e, n=name: self._draw_left_hero(n))

        # Right side panel
        right = tk.Frame(frame, bg=self.colors["panel"],
                         highlightbackground=self.colors["border"],
                         highlightcolor=self.colors["border"],
                         highlightthickness=2, bd=0)
        right.place(relx=0.57, rely=0.05, relwidth=0.38, relheight=0.9)
        self.right_panels[name] = right

        # Title on right
        title_lbl = tk.Label(
            right,
            text=title,
            font=("Segoe UI Semibold", 22),
            fg=self.colors["text_primary"],
            bg=self.colors["panel"]
        )
        title_lbl.pack(pady=(10, 14))
        self.titles[name] = title_lbl

    def _set_title(self, name, text):
        self.titles[name].config(text=text)

    def _draw_left_hero(self, name):
        # Get the canvas safely
        c = self.left_canvases.get(name)
        # Exit if canvas is missing or destroyed
        if not c or not c.winfo_exists():
            return

        # Now safe to clear and redraw
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        cx = int(w * 0.35)
        cy = int(h * 0.5)
        max_r = min(w, h) // 2

        rings = [
            (int(max_r * 0.75), self.colors["ring1"]),
            (int(max_r * 0.62), self.colors["ring2"]),
            (int(max_r * 0.5), self.colors["ring3"]),
            (int(max_r * 0.4), self.colors["ring4"]),
        ]
        for r, col in rings:
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=2)

        inner_rs = [int(max_r * 0.32), int(max_r * 0.26)]
        for r in inner_rs:
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#0f1c2e", outline="")

        rupee_size = int(min(w, h) * 0.16)
        c.create_text(cx, cy, text="₹", fill=self.colors["ring4"], font=("Segoe UI", rupee_size, "bold"))

        c.create_text(40, 30, anchor="nw",
                      text="WELCOME TO UNITY BANK",
                      fill=self.colors["text_primary"],
                      font=("Segoe UI", 18, "bold"))

    # -------------------- Navigation --------------------
    def show_frame(self, name):
        # Special layout for full-width customer transactions
        if name == "cust_transactions":
            # Hide left hero and right panel
            self.left_canvases[name].place_forget()
            self.right_panels[name].place_forget()
        else:
            # Restore default layout
            self.left_canvases[name].place(relx=0, rely=0, relwidth=0.55, relheight=1)
            self.right_panels[name].place(relx=0.57, rely=0.05, relwidth=0.38, relheight=0.9)

        self.frames[name].tkraise()
        if name == "create_acc":
            self.refresh_cust_ids()
            self.refresh_cust_names()

    def logout(self):
        if hasattr(self, 'emp_email'): self.emp_email.delete(0, 'end')
        if hasattr(self, 'emp_pass'): self.emp_pass.delete(0, 'end')
        if hasattr(self, 'cust_acc'): self.cust_acc.delete(0, 'end')
        if hasattr(self, 'cust_pin'): self.cust_pin.delete(0, 'end')
        self.emp_name = None
        self.cust_name = None
        self.cust_acc_no = None
        self.show_frame("main")

    # ==================== Main ====================
    def create_main(self):
        name = "main"
        self._set_title(name, "Welcome")
        right = self.right_panels[name]

        tk.Label(right, text="Choose an option", fg=self.colors["text_muted"],
                 bg=self.colors["panel"], font=("Segoe UI", 12)).pack(pady=(0, 8))

        ttk.Button(right, text="Employee Login", style="Secondary.TButton",
                   command=lambda: self.show_frame("emp_login")).pack(fill="x", padx=20, pady=6)

        ttk.Button(right, text="Customer Login", style="Secondary.TButton",
                   command=lambda: self.show_frame("cust_login")).pack(fill="x", padx=20, pady=6)

        ttk.Button(right, text="Logout / Exit", style="Danger.TButton",
                   command=self.root.destroy).pack(fill="x", padx=20, pady=12)

    # ==================== Employee Login ====================
    def create_emp_login(self):
        name = "emp_login"
        self._set_title(name, "Employee login")
        right = self.right_panels[name]

        def add_row(label):
            tk.Label(right, text=label, fg=self.colors["text_muted"], bg=self.colors["panel"],
                     font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(6, 2))

        add_row("Email")
        self.emp_email = ttk.Entry(right, style="Dark.TEntry"); self.emp_email.pack(fill="x", padx=20, pady=(0, 6))

        add_row("Password")
        self.emp_pass = ttk.Entry(right, style="Dark.TEntry", show="*"); self.emp_pass.pack(fill="x", padx=20, pady=(0, 10))

        ttk.Button(right, text="Login", style="Secondary.TButton", command=self.employee_login).pack(fill="x", padx=20, pady=6)
        ttk.Button(right, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("main")).pack(fill="x", padx=20, pady=6)

    def employee_login(self):
        email = self.emp_email.get().strip()
        password = self.emp_pass.get().strip()
        if not email or not password:
            messagebox.showerror("Error", "Fill all fields")
            return
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("SELECT emp_id, name FROM employees WHERE email=%s AND password=%s", (email, password))
            res = cur.fetchone()
            db.close()
            if res:
                self.emp_name = res[1]
                self.emp_welcome.config(text=f"Welcome Employee: {self.emp_name}")
                self.show_frame("emp_dash")
            else:
                messagebox.showerror("Error", "Invalid Email or Password")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Customer Login ====================
    def create_cust_login(self):
        name = "cust_login"
        self._set_title(name, "Customer login")
        right = self.right_panels[name]

        def add_row(label):
            tk.Label(right, text=label, fg=self.colors["text_muted"], bg=self.colors["panel"],
                     font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(6, 2))

        add_row("Email")
        self.cust_email = ttk.Entry(right, style="Dark.TEntry")
        self.cust_email.pack(fill="x", padx=20, pady=(0, 6))

        add_row("Password")
        self.cust_pass = ttk.Entry(right, style="Dark.TEntry", show="*")
        self.cust_pass.pack(fill="x", padx=20, pady=(0, 10))

        ttk.Button(right, text="Login", style="Secondary.TButton", command=self.customer_login).pack(fill="x", padx=20,
                                                                                                     pady=6)
        ttk.Button(right, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("main")).pack(
            fill="x", padx=20, pady=6)

    def customer_login(self):
        email = self.cust_email.get().strip()
        password = self.cust_pass.get().strip()
        if not email or not password:
            messagebox.showerror("Error", "Fill all fields")
            return
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("""
                SELECT a.account_no, c.name, a.status
                FROM accounts a
                JOIN customers c ON a.cust_id = c.cust_id
                WHERE c.email=%s AND c.password=%s
            """, (email, password))
            res = cur.fetchone()
            db.close()
            if res:
                if res[2] != "Active":
                    messagebox.showerror("Error", "Account is blocked. Contact bank.")
                    return
                self.cust_name = res[1]
                self.cust_acc_no = res[0]
                self.cust_welcome.config(text=f"Welcome Customer: {self.cust_name}")
                self.show_frame("cust_dash")
            else:
                messagebox.showerror("Error", "Invalid Email or Password")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Employee Dashboard ====================
    def create_emp_dashboard(self):
        name = "emp_dash"
        self._set_title(name, "Employee dashboard")
        right = self.right_panels[name]

        self.emp_welcome = tk.Label(right, text="Welcome Employee", font=("Segoe UI", 16, "bold"),
                                    fg=self.colors["text_primary"], bg=self.colors["panel"])
        self.emp_welcome.pack(pady=(0, 10))

        buttons = [
            ("Add New Customer", lambda: self.show_frame("add_cust")),
            ("Create Bank Account", lambda: self.show_frame("create_acc")),
            ("Deposit Amount", lambda: self.show_frame("deposit")),
            ("Withdraw Amount", lambda: self.show_frame("withdraw")),
            ("View Customers & Accounts", self.view_all_accounts),
            ("Block / Unblock Account", lambda: self.show_frame("block")),
            ("View Transactions", lambda: self.show_frame("transactions")),
        ]
        for text, cmd in buttons:
            ttk.Button(right, text=text, style="Secondary.TButton", command=cmd).pack(fill="x", padx=20, pady=6)

        ttk.Button(right, text="Logout", style="Danger.TButton", command=self.logout).pack(fill="x", padx=20, pady=8)

    # ==================== Customer Dashboard ====================
    def create_cust_dashboard(self):
        name = "cust_dash"
        self._set_title(name, "Customer dashboard")
        right = self.right_panels[name]

        self.cust_welcome = tk.Label(right, text="Welcome Customer", font=("Segoe UI", 16, "bold"),
                                     fg=self.colors["text_primary"], bg=self.colors["panel"])
        self.cust_welcome.pack(pady=(0, 10))

        buttons = [
            ("View Balance", lambda: self.show_frame("cust_balance")),
            ("Deposit", lambda: self.show_frame("cust_deposit")),
            ("Withdraw", lambda: self.show_frame("cust_withdraw")),
            ("Transfer Money", lambda: self.show_frame("transfer")),
            ("View Transactions", lambda: self.show_frame("cust_transactions")),
            ("Change PIN", lambda: self.show_frame("pin_change")),
            ("Send WhatsApp Summary", self.customer_send_whatsapp_summary),
        ]
        for text, cmd in buttons:
            ttk.Button(right, text=text, style="Secondary.TButton", command=cmd).pack(fill="x", padx=20, pady=6)

        ttk.Button(right, text="Logout", style="Danger.TButton", command=self.logout).pack(fill="x", padx=20, pady=8)

    # ==================== Add Customer (KYC) ====================
    def create_add_customer(self):
        name = "add_cust"
        self._set_title(name, "Add customer (KYC)")
        right = self.right_panels[name]

        form = tk.Frame(right, bg=self.colors["panel"])
        form.pack(fill="both", expand=True, padx=20, pady=(5, 0))  # tighter top padding

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 1))  # reduced spacing

        add_row("First Name")
        self.first_name = ttk.Entry(form, style="Dark.TEntry");
        self.first_name.pack(fill="x", pady=(0, 2))

        add_row("Last Name")
        self.last_name = ttk.Entry(form, style="Dark.TEntry");
        self.last_name.pack(fill="x", pady=(0, 2))

        add_row("Gender")
        self.gender = ttk.Combobox(form, values=["Male", "Female", "Other"], style="Dark.TCombobox")
        self.gender.pack(fill="x", pady=(0, 2))

        add_row("DOB (YYYY-MM-DD)")
        self.dob = ttk.Entry(form, style="Dark.TEntry");
        self.dob.pack(fill="x", pady=(0, 2))

        add_row("Mobile (10 digits)")
        self.mobile = ttk.Entry(form, style="Dark.TEntry");
        self.mobile.pack(fill="x", pady=(0, 2))

        add_row("Email")
        self.email = ttk.Entry(form, style="Dark.TEntry");
        self.email.pack(fill="x", pady=(0, 2))

        add_row("Password")
        self.password = ttk.Entry(form, style="Dark.TEntry", show="*");
        self.password.pack(fill="x", pady=(0, 2))

        add_row("Address")
        self.address = tk.Text(form, height=3, bg=self.colors["panel"], fg=self.colors["text_primary"],
                               insertbackground=self.colors["text_primary"], relief="solid",
                               highlightbackground=self.colors["border"], highlightthickness=1, bd=0)
        self.address.pack(fill="x", pady=(0, 4))

        # Compact button row
        btn_row = tk.Frame(right, bg=self.colors["panel"])
        btn_row.pack(fill="x", padx=20, pady=(4, 2))  # reduced bottom padding

        ttk.Button(btn_row, text="Add Customer", style="Secondary.TButton",
                   command=self.add_customer).pack(side="left", expand=True, fill="x", padx=(0, 4), ipady=1)

        ttk.Button(btn_row, text="Back", style="Secondary.TButton",
                   command=lambda: self.show_frame("emp_dash")).pack(side="left", expand=True, fill="x", padx=(4, 0),
                                                                     ipady=1)

    def add_customer(self):
        fname = self.first_name.get().strip()
        lname = self.last_name.get().strip()
        gender = self.gender.get().strip()
        dob = self.dob.get().strip()
        mobile = self.mobile.get().strip()
        email = self.email.get().strip()
        addr = self.address.get("1.0", "end").strip()
        password = self.password.get().strip()  # NEW

        if not all([fname, lname, gender, dob, mobile, email, addr, password]):
            messagebox.showerror("Error", "Fill all fields")
            return
        if not is_valid_date(dob):
            messagebox.showerror("Error", "Invalid DOB format (YYYY-MM-DD)")
            return
        if not is_valid_mobile(mobile):
            messagebox.showerror("Error", "Mobile must be 10 digits")
            return

        name = f"{fname} {lname}"
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("""
                INSERT INTO customers(name, gender, dob, mobile, email, address, password)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (name, gender, dob, mobile, email, addr, password))
            db.commit()
            cur.execute("SELECT LAST_INSERT_ID()")
            cust_id = cur.fetchone()[0]
            db.close()
            messagebox.showinfo("Success", f"Customer Added! ID: {cust_id}")

            # clear fields
            self.first_name.delete(0, 'end')
            self.last_name.delete(0, 'end')
            self.gender.set('')
            self.dob.delete(0, 'end')
            self.mobile.delete(0, 'end')
            self.email.delete(0, 'end')
            self.address.delete("1.0", 'end')
            self.password.delete(0, 'end')  # NEW
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Create Bank Account ====================
    def create_create_account(self):
        name = "create_acc"
        self._set_title(name, "Create bank account")
        right = self.right_panels[name]

        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Customer ID")
        self.ca_cust_id = ttk.Combobox(form, width=28, values=self.fetch_customer_ids(), style="Dark.TCombobox"); self.ca_cust_id.pack(fill="x")

        add_row("Or Customer Name")
        self.ca_cust_name = ttk.Combobox(form, width=28, values=self.fetch_customer_names(), style="Dark.TCombobox"); self.ca_cust_name.pack(fill="x")

        add_row("Account Type")
        self.ca_type = ttk.Combobox(form, values=["Savings","Current"], style="Dark.TCombobox"); self.ca_type.pack(fill="x")

        add_row("PIN (min 4 digits)")
        self.ca_pin = ttk.Entry(form, style="Dark.TEntry"); self.ca_pin.pack(fill="x")

        add_row("Initial Deposit")
        self.ca_deposit = ttk.Entry(form, style="Dark.TEntry"); self.ca_deposit.pack(fill="x")

        add_row("Contact (auto from customer)")
        self.ca_contact_lbl = tk.Label(form, text="-", bg=self.colors["panel"], fg=self.colors["text_primary"], font=("Segoe UI", 10))
        self.ca_contact_lbl.pack(anchor="w", pady=(0,4))

        small_row = tk.Frame(form, bg=self.colors["panel"]); small_row.pack(fill="x", pady=(6,0))
        ttk.Button(small_row, text="Load Contact", style="Secondary.TButton", command=self.load_selected_contact).pack(side="left", fill="x", expand=True, padx=(0,6))
        ttk.Button(small_row, text="Create Account", style="Secondary.TButton", command=self.create_account).pack(side="left", fill="x", expand=True, padx=(6,0))

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Refresh Customers", style="Secondary.TButton", command=self.refresh_customers).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("emp_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def fetch_customer_ids(self):
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("SELECT cust_id FROM customers ORDER BY cust_id")
            ids = [str(r[0]) for r in cur.fetchall()]
            db.close()
            return ids
        except:
            return []

    def fetch_customer_names(self):
        try:
            db = connect_db()
            cur = db.cursor()
            cur.execute("SELECT name FROM customers ORDER BY name")
            names = [r[0] for r in cur.fetchall()]
            db.close()
            return names
        except:
            return []

    def refresh_cust_ids(self):
        self.ca_cust_id['values'] = self.fetch_customer_ids()

    def refresh_cust_names(self):
        self.ca_cust_name['values'] = self.fetch_customer_names()

    def refresh_customers(self):
        self.refresh_cust_ids()
        self.refresh_cust_names()

    def load_selected_contact(self):
        cust_id = self.ca_cust_id.get().strip()
        name = self.ca_cust_name.get().strip()
        try:
            db = connect_db()
            cur = db.cursor()
            if cust_id:
                cur.execute("SELECT name, mobile, email FROM customers WHERE cust_id=%s", (cust_id,))
            elif name:
                cur.execute("SELECT name, mobile, email, cust_id FROM customers WHERE name=%s", (name,))
            else:
                messagebox.showerror("Error", "Select Customer ID or Name")
                return
            row = cur.fetchone()
            db.close()
            if not row:
                messagebox.showerror("Error", "Customer not found")
                return
            if cust_id:
                cname, mobile, email = row
            else:
                cname, mobile, email, cid = row
                self.ca_cust_id.set(str(cid))
            self.ca_cust_name.set(cname)
            self.ca_contact_lbl.config(text=f"{cname} | {mobile} | {email}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_account(self):
        cust_id = self.ca_cust_id.get().strip()
        acc_type = self.ca_type.get().strip()
        pin = self.ca_pin.get().strip()
        deposit = self.ca_deposit.get().strip()

        if not all([cust_id, acc_type, pin, deposit]):
            messagebox.showerror("Error", "Fill all fields")
            return
        if len(pin) < 4 or not pin.isdigit():
            messagebox.showerror("Error", "PIN must be at least 4 digits")
            return
        if not is_positive_amount(deposit):
            messagebox.showerror("Error", "Initial deposit must be positive")
            return

        acc_no = generate_acc_no()
        ifsc = generate_ifsc()
        try:
            db = connect_db()
            cur = db.cursor()

            cur.execute("SELECT name FROM customers WHERE cust_id=%s", (cust_id,))
            cust_name_row = cur.fetchone()
            if not cust_name_row:
                db.close()
                messagebox.showerror("Error", "Customer not found")
                return
            cust_name = cust_name_row[0]

            cur.execute("""
                INSERT INTO accounts(account_no, cust_id, cust_name, account_type, pin, balance, ifsc, status)
                VALUES(%s,%s,%s,%s,%s,%s,%s,'Active')
            """, (acc_no, cust_id, cust_name, acc_type, pin, sanitize_amount(deposit), ifsc))

            cur.execute("""
                INSERT INTO transactions(account_no, cust_name, txn_type, amount)
                VALUES (%s,%s,%s,%s)
            """, (acc_no, cust_name, "Deposit", sanitize_amount(deposit)))

            db.commit()
            db.close()

            messagebox.showinfo("Success", f"Account Created!\nAccount No: {acc_no}\nIFSC: {ifsc}")
            self.ca_cust_id.set('')
            self.ca_cust_name.set('')
            self.ca_type.set('')
            self.ca_pin.delete(0, 'end')
            self.ca_deposit.delete(0, 'end')
            self.ca_contact_lbl.config(text='-')

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Deposit (Employee) ====================
    def create_deposit(self):
        name = "deposit"
        self._set_title(name, "Deposit amount (employee)")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.dep_acc = ttk.Entry(form, style="Dark.TEntry"); self.dep_acc.pack(fill="x")

        add_row("Customer Name")
        self.dep_name = ttk.Entry(form, style="Dark.TEntry"); self.dep_name.pack(fill="x")

        add_row("PIN")
        self.dep_pin = ttk.Entry(form, style="Dark.TEntry", show="*"); self.dep_pin.pack(fill="x")

        add_row("Amount")
        self.dep_amt = ttk.Entry(form, style="Dark.TEntry"); self.dep_amt.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Deposit", style="Secondary.TButton", command=self.deposit_amount).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("emp_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def deposit_amount(self):
        acc = self.dep_acc.get().strip()
        name = self.dep_name.get().strip()
        pin = self.dep_pin.get().strip()
        amt = self.dep_amt.get().strip()
        if not all([acc, name, pin, amt]):
            messagebox.showerror("Error", "Fill all fields"); return
        if not is_positive_amount(amt):
            messagebox.showerror("Error", "Amount must be positive"); return
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("""
                SELECT c.name, a.status, a.pin
                FROM accounts a JOIN customers c ON a.cust_id=c.cust_id
                WHERE a.account_no=%s
            """, (acc,))
            row = cur.fetchone()
            if not row:
                db.close(); messagebox.showerror("Error", "Account not found"); return
            db_name, status, real_pin = row
            if status != "Active":
                db.close(); messagebox.showerror("Error", "Account is blocked"); return
            if db_name.strip().lower() != name.strip().lower():
                db.close(); messagebox.showerror("Error", "Name does not match account"); return
            if real_pin != pin:
                db.close(); messagebox.showerror("Error", "Incorrect PIN"); return

            cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_no=%s", (sanitize_amount(amt), acc))
            cur.execute("INSERT INTO transactions(account_no, cust_name, txn_type, amount) VALUES (%s,%s,%s,%s)", (acc, db_name, "Deposit", sanitize_amount(amt)))
            db.commit(); db.close()
            messagebox.showinfo("Success", "Deposit successful")
            self.dep_amt.delete(0,'end')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Withdraw (Employee) ====================
    def create_withdraw(self):
        name = "withdraw"
        self._set_title(name, "Withdraw amount (employee)")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.wd_acc = ttk.Entry(form, style="Dark.TEntry"); self.wd_acc.pack(fill="x")

        add_row("Customer Name")
        self.wd_name = ttk.Entry(form, style="Dark.TEntry"); self.wd_name.pack(fill="x")

        add_row("PIN")
        self.wd_pin = ttk.Entry(form, style="Dark.TEntry", show="*"); self.wd_pin.pack(fill="x")

        add_row("Amount")
        self.wd_amt = ttk.Entry(form, style="Dark.TEntry"); self.wd_amt.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Withdraw", style="Secondary.TButton", command=self.withdraw_amount).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("emp_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def withdraw_amount(self):
        acc = self.wd_acc.get().strip()
        name = self.wd_name.get().strip()
        pin = self.wd_pin.get().strip()
        amt = self.wd_amt.get().strip()
        if not all([acc, name, pin, amt]):
            messagebox.showerror("Error", "Fill all fields"); return
        if not is_positive_amount(amt):
            messagebox.showerror("Error", "Amount must be positive"); return
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("""
                SELECT c.name, a.status, a.pin, a.balance
                FROM accounts a JOIN customers c ON a.cust_id=c.cust_id
                WHERE a.account_no=%s
            """, (acc,))
            row = cur.fetchone()
            if not row:
                db.close(); messagebox.showerror("Error", "Account not found"); return
            db_name, status, real_pin, bal = row
            if status != "Active":
                db.close(); messagebox.showerror("Error", "Account is blocked"); return
            if db_name.strip().lower() != name.strip().lower():
                db.close(); messagebox.showerror("Error", "Name does not match account"); return
            if real_pin != pin:
                db.close(); messagebox.showerror("Error", "Incorrect PIN"); return
            if float(bal) < float(amt):
                db.close(); messagebox.showerror("Error", "Insufficient balance"); return

            cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_no=%s", (sanitize_amount(amt), acc))
            cur.execute("INSERT INTO transactions(account_no, cust_name, txn_type, amount) VALUES (%s,%s,%s,%s)", (acc, db_name, "Withdraw", sanitize_amount(amt)))
            db.commit(); db.close()
            messagebox.showinfo("Success", "Withdrawal successful")
            self.wd_amt.delete(0,'end')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Block / Unblock ====================
    def create_block_account(self):
        name = "block"
        self._set_title(name, "Block / Unblock account")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.blk_acc = ttk.Entry(form, style="Dark.TEntry"); self.blk_acc.pack(fill="x")

        add_row("Status")
        self.blk_status = ttk.Combobox(form, values=["Active", "Blocked"], style="Dark.TCombobox"); self.blk_status.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Update Status", style="Secondary.TButton", command=self.update_account_status).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("emp_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def update_account_status(self):
        acc = self.blk_acc.get().strip()
        status = self.blk_status.get().strip()
        if not acc or status not in ["Active", "Blocked"]:
            messagebox.showerror("Error", "Provide account number and valid status"); return
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("UPDATE accounts SET status=%s WHERE account_no=%s", (status, acc))
            if cur.rowcount == 0:
                db.close(); messagebox.showerror("Error", "Account not found"); return
            db.commit(); db.close()
            messagebox.showinfo("Success", f"Account status set to {status}")
            self.blk_acc.delete(0,'end'); self.blk_status.set('')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Transactions (Employee) ====================
    def create_transactions(self):
        name = "transactions"
        self._set_title(name, "Transaction history (employee)")
        right = self.right_panels[name]

        tk.Label(right, text="Account Number (optional)", fg=self.colors["text_muted"], bg=self.colors["panel"],
                 font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(0, 6))
        self.txn_acc = ttk.Entry(right, style="Dark.TEntry")
        self.txn_acc.pack(fill="x", padx=20, pady=(0, 6))

        ttk.Button(right, text="Load", style="Secondary.TButton", command=self.view_transactions).pack(fill="x", padx=20, pady=6)
        ttk.Button(right, text="Send WhatsApp Summary", style="Secondary.TButton",
                   command=self.employee_send_whatsapp_summary).pack(fill="x", padx=20, pady=6)

        tv_frame = tk.Frame(right, bg=self.colors["panel"])
        tv_frame.pack(fill="both", expand=True, padx=20, pady=6)

        tv_scroll_y = ttk.Scrollbar(tv_frame, orient="vertical")
        tv_scroll_x = ttk.Scrollbar(tv_frame, orient="horizontal")
        self.txn_tree = ttk.Treeview(
            tv_frame, style="Dark.Treeview",
            columns=("Txn ID","Account No","Name","Type","Amount","Date"), show="headings",
            yscrollcommand=tv_scroll_y.set, xscrollcommand=tv_scroll_x.set
        )
        tv_scroll_y.config(command=self.txn_tree.yview)
        tv_scroll_x.config(command=self.txn_tree.xview)
        tv_scroll_y.pack(side="right", fill="y")
        tv_scroll_x.pack(side="bottom", fill="x")
        self.txn_tree.pack(fill="both", expand=True)

        for col, w in [("Txn ID",80),("Account No",150),("Name",180),("Type",120),("Amount",120),("Date",220)]:
            self.txn_tree.heading(col, text=col); self.txn_tree.column(col, width=w, minwidth=80, stretch=True)

        back_row = tk.Frame(right, bg=self.colors["panel"])
        back_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(back_row, text="Back", style="Secondary.TButton",
                   command=lambda: self.show_frame("emp_dash")).pack(fill="x")

    def view_transactions(self):
        acc = self.txn_acc.get().strip()
        try:
            db = connect_db(); cur = db.cursor()
            if acc:
                cur.execute("""
                    SELECT txn_id, account_no, cust_name, txn_type, amount, txn_date
                    FROM transactions
                    WHERE account_no=%s
                    ORDER BY txn_date ASC, txn_id ASC
                """, (acc,))
            else:
                cur.execute("""
                    SELECT txn_id, account_no, cust_name, txn_type, amount, txn_date
                    FROM transactions
                    ORDER BY txn_date ASC, txn_id ASC
                    LIMIT 200
                """)
            rows = cur.fetchall(); db.close()
            for i in self.txn_tree.get_children(): self.txn_tree.delete(i)
            for r in rows: self.txn_tree.insert("", "end", values=r)
            if not rows:
                messagebox.showinfo("Info", "No transactions found")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Customer Deposit ====================
    def create_cust_deposit(self):
        name = "cust_deposit"
        self._set_title(name, "Deposit (customer)")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.cdep_acc = ttk.Entry(form, style="Dark.TEntry"); self.cdep_acc.pack(fill="x")
        add_row("Name")
        self.cdep_name = ttk.Entry(form, style="Dark.TEntry"); self.cdep_name.pack(fill="x")
        add_row("PIN")
        self.cdep_pin = ttk.Entry(form, style="Dark.TEntry", show="*"); self.cdep_pin.pack(fill="x")
        add_row("Amount")
        self.cdep_amt = ttk.Entry(form, style="Dark.TEntry"); self.cdep_amt.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Deposit", style="Secondary.TButton", command=self.cust_deposit_amount).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("cust_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def cust_deposit_amount(self):
        acc = self.cdep_acc.get().strip()
        name = self.cdep_name.get().strip()
        pin = self.cdep_pin.get().strip()
        amt = self.cdep_amt.get().strip()
        if not all([acc, name, pin, amt]):
            messagebox.showerror("Error","Fill all fields"); return
        if not is_positive_amount(amt):
            messagebox.showerror("Error","Amount must be positive"); return
        self._money_op(acc, name, pin, amt, op="Deposit")

    # ==================== Customer Withdraw ====================
    def create_cust_withdraw(self):
        name = "cust_withdraw"
        self._set_title(name, "Withdraw (customer)")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.cwd_acc = ttk.Entry(form, style="Dark.TEntry"); self.cwd_acc.pack(fill="x")
        add_row("Name")
        self.cwd_name = ttk.Entry(form, style="Dark.TEntry"); self.cwd_name.pack(fill="x")
        add_row("PIN")
        self.cwd_pin = ttk.Entry(form, style="Dark.TEntry", show="*"); self.cwd_pin.pack(fill="x")
        add_row("Amount")
        self.cwd_amt = ttk.Entry(form, style="Dark.TEntry"); self.cwd_amt.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Withdraw", style="Secondary.TButton", command=self.cust_withdraw_amount).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("cust_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def cust_withdraw_amount(self):
        acc = self.cwd_acc.get().strip()
        name = self.cwd_name.get().strip()
        pin = self.cwd_pin.get().strip()
        amt = self.cwd_amt.get().strip()
        if not all([acc, name, pin, amt]):
            messagebox.showerror("Error","Fill all fields"); return
        if not is_positive_amount(amt):
            messagebox.showerror("Error","Amount must be positive"); return
        self._money_op(acc, name, pin, amt, op="Withdraw")

    def _money_op(self, acc, name, pin, amt, op="Deposit"):
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("""
                SELECT c.name, a.status, a.pin, a.balance
                FROM accounts a JOIN customers c ON a.cust_id=c.cust_id
                WHERE a.account_no=%s
            """, (acc,))
            row = cur.fetchone()
            if not row:
                db.close(); messagebox.showerror("Error","Account not found"); return
            db_name, status, real_pin, bal = row
            if status != "Active":
                db.close(); messagebox.showerror("Error","Account is blocked"); return
            if db_name.strip().lower() != name.strip().lower():
                db.close(); messagebox.showerror("Error","Name does not match account"); return
            if real_pin != pin:
                db.close(); messagebox.showerror("Error","Incorrect PIN"); return
            if op == "Withdraw" and float(bal) < float(amt):
                db.close(); messagebox.showerror("Error","Insufficient balance"); return

            if op == "Deposit":
                cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_no=%s", (sanitize_amount(amt), acc))
            else:
                cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_no=%s", (sanitize_amount(amt), acc))
            cur.execute("INSERT INTO transactions(account_no, cust_name, txn_type, amount) VALUES (%s,%s,%s,%s)", (acc, db_name, op, sanitize_amount(amt)))
            db.commit(); db.close()
            messagebox.showinfo("Success", f"{op} successful")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Customer Transactions (Full-width) ====================
    def create_cust_transactions(self):
        name = "cust_transactions"
        frame = self.frames[name]

        # FULL-WIDTH layout (hide default right panel; build custom)
        for child in frame.winfo_children():
            child.destroy()

        # Title bar
        title_bar = tk.Frame(frame, bg=self.colors["panel"], highlightbackground=self.colors["border"],
                             highlightthickness=2)
        title_bar.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(title_bar, text="Transaction history (customer)",
                 font=("Segoe UI Semibold", 22),
                 fg=self.colors["text_primary"], bg=self.colors["panel"]).pack(side="left", padx=10, pady=10)
        ttk.Button(title_bar, text="Back", style="Secondary.TButton",
                   command=lambda: self.show_frame("cust_dash")).pack(side="right", padx=10, pady=10)

        # Search row
        search_bar = tk.Frame(frame, bg=self.colors["bg"])
        search_bar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(search_bar, text="Account Number", fg=self.colors["text_muted"], bg=self.colors["bg"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(0, 10))
        self.ctx_acc = ttk.Entry(search_bar, style="Dark.TEntry", width=30)
        self.ctx_acc.pack(side="left")
        ttk.Button(search_bar, text="Load", style="Secondary.TButton",
                   command=self.view_cust_transactions).pack(side="left", padx=10)

        # Tree container with scrollbars (fills entire width)
        table_wrap = tk.Frame(frame, bg=self.colors["bg"])
        table_wrap.pack(fill="both", expand=True, padx=20, pady=10)

        ctx_scroll_y = ttk.Scrollbar(table_wrap, orient="vertical")
        ctx_scroll_x = ttk.Scrollbar(table_wrap, orient="horizontal")
        self.ctx_tree = ttk.Treeview(
            table_wrap, style="Dark.Treeview",
            columns=("Txn ID","Account No","Name","Type","Amount","Date"),
            show="headings",
            yscrollcommand=ctx_scroll_y.set,
            xscrollcommand=ctx_scroll_x.set
        )
        ctx_scroll_y.config(command=self.ctx_tree.yview)
        ctx_scroll_x.config(command=self.ctx_tree.xview)
        ctx_scroll_y.pack(side="right", fill="y")
        ctx_scroll_x.pack(side="bottom", fill="x")
        self.ctx_tree.pack(fill="both", expand=True)

        for col, w in [("Txn ID",100),("Account No",180),("Name",220),("Type",140),("Amount",140),("Date",240)]:
            self.ctx_tree.heading(col, text=col)
            self.ctx_tree.column(col, width=w, minwidth=100, stretch=True)

    def view_cust_transactions(self):
        acc = self.ctx_acc.get().strip()
        if not acc:
            messagebox.showerror("Error", "Enter account number"); return
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("""
                SELECT txn_id, account_no, cust_name, txn_type, amount, txn_date
                FROM transactions
                WHERE account_no=%s
                ORDER BY txn_date ASC, txn_id ASC
            """, (acc,))
            rows = cur.fetchall(); db.close()
            for i in self.ctx_tree.get_children(): self.ctx_tree.delete(i)
            for r in rows: self.ctx_tree.insert("", "end", values=r)
            if not rows:
                messagebox.showinfo("Info", "No transactions found")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Customer Balance ====================
    def create_cust_balance(self):
        name = "cust_balance"
        self._set_title(name, "View balance (customer)")
        right = self.right_panels[name]

        tk.Label(right, text="Account Number", fg=self.colors["text_muted"], bg=self.colors["panel"],
                 font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(0, 6))
        self.vb_acc = ttk.Entry(right, style="Dark.TEntry"); self.vb_acc.pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(right, text="PIN", fg=self.colors["text_muted"], bg=self.colors["panel"],
                 font=("Segoe UI", 11)).pack(anchor="w", padx=20, pady=(0, 6))
        self.vb_pin = ttk.Entry(right, style="Dark.TEntry", show="*"); self.vb_pin.pack(fill="x", padx=20, pady=(0, 10))

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Check Balance", style="Secondary.TButton", command=self.view_balance).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("cust_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def view_balance(self):
        acc = self.vb_acc.get().strip()
        pin = self.vb_pin.get().strip()
        if not acc or not pin:
            messagebox.showerror("Error","Enter account and PIN"); return
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("SELECT balance, status, pin FROM accounts WHERE account_no=%s", (acc,))
            row = cur.fetchone(); db.close()
            if not row:
                messagebox.showerror("Error","Account not found"); return
            bal, status, real_pin = row
            if status != "Active":
                messagebox.showerror("Error","Account is blocked"); return
            if real_pin != pin:
                messagebox.showerror("Error","Incorrect PIN"); return
            messagebox.showinfo("Balance", f"Your Balance: ₹{bal}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Employee: View Customers & Accounts ====================
    def view_all_accounts(self):
        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("""
                SELECT c.cust_id, c.name, c.mobile, a.account_no, a.account_type, a.balance, a.status
                FROM customers c
                LEFT JOIN accounts a ON c.cust_id = a.cust_id
                ORDER BY c.cust_id ASC
            """)
            rows = cur.fetchall(); db.close()

            win = tk.Toplevel(self.root); win.title("Customers & Accounts"); win.geometry("1000x500")
            win.configure(bg=self.colors["bg"])
            tv_frame = tk.Frame(win, bg=self.colors["bg"]); tv_frame.pack(fill="both", expand=True, padx=20, pady=20)

            scroll_y = ttk.Scrollbar(tv_frame, orient="vertical")
            scroll_x = ttk.Scrollbar(tv_frame, orient="horizontal")
            tv = ttk.Treeview(tv_frame, style="Dark.Treeview",
                              columns=("Cust ID","Name","Mobile","Account No","Type","Balance","Status"),
                              show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
            scroll_y.config(command=tv.yview)
            scroll_x.config(command=tv.xview)
            scroll_y.pack(side="right", fill="y")
            scroll_x.pack(side="bottom", fill="x")
            tv.pack(fill="both", expand=True)

            for col, w in [("Cust ID",80),("Name",180),("Mobile",120),("Account No",150),("Type",100),("Balance",100),("Status",100)]:
                tv.heading(col, text=col); tv.column(col, width=w, stretch=True)

            for row in rows:
                tv.insert("", "end", values=row)

            if not rows:
                messagebox.showinfo("Info", "No records found")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Customer: Send WhatsApp Summary ====================
    def customer_send_whatsapp_summary(self):
        if not self.cust_acc_no:
            messagebox.showerror("Error", "Please login as customer first."); return
        mobile, msg, err = build_whatsapp_summary(self.cust_acc_no)
        if err:
            messagebox.showerror("Error", err); return
        err2 = send_whatsapp_message(mobile, msg)
        if err2:
            messagebox.showerror("Error", err2)
        else:
            messagebox.showinfo("Success", "WhatsApp summary sent successfully.")

    # ==================== Employee: Send WhatsApp Summary ====================
    def employee_send_whatsapp_summary(self):
        acc = self.txn_acc.get().strip()
        if not acc:
            messagebox.showerror("Error", "Enter an account number above to send summary."); return
        mobile, msg, err = build_whatsapp_summary(acc)
        if err:
            messagebox.showerror("Error", err); return
        err2 = send_whatsapp_message(mobile, msg)
        if err2:
            messagebox.showerror("Error", err2)
        else:
            messagebox.showinfo("Success", "WhatsApp summary sent successfully.")

    # ==================== Transfer Money ====================
    def create_transfer(self):
        name = "transfer"
        self._set_title(name, "Transfer money")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("From Account")
        self.tr_from = ttk.Entry(form, style="Dark.TEntry"); self.tr_from.pack(fill="x")

        add_row("Name (from account)")
        self.tr_name = ttk.Entry(form, style="Dark.TEntry"); self.tr_name.pack(fill="x")

        add_row("PIN (from account)")
        self.tr_pin = ttk.Entry(form, style="Dark.TEntry", show="*"); self.tr_pin.pack(fill="x")

        add_row("To Account")
        self.tr_to = ttk.Entry(form, style="Dark.TEntry"); self.tr_to.pack(fill="x")

        add_row("Amount")
        self.tr_amt = ttk.Entry(form, style="Dark.TEntry"); self.tr_amt.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Transfer", style="Secondary.TButton", command=self.transfer_money).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("cust_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def transfer_money(self):
        acc_from = self.tr_from.get().strip()
        name = self.tr_name.get().strip()
        pin = self.tr_pin.get().strip()
        acc_to = self.tr_to.get().strip()
        amt = self.tr_amt.get().strip()

        if not all([acc_from, name, pin, acc_to, amt]):
            messagebox.showerror("Error", "Fill all fields"); return
        if acc_from == acc_to:
            messagebox.showerror("Error", "From and To accounts must be different"); return
        if not is_positive_amount(amt):
            messagebox.showerror("Error", "Amount must be positive"); return

        try:
            db = connect_db(); cur = db.cursor()

            cur.execute("""
                SELECT c.name, a.status, a.pin, a.balance
                FROM accounts a JOIN customers c ON a.cust_id=c.cust_id
                WHERE a.account_no=%s
            """, (acc_from,))
            row_from = cur.fetchone()
            if not row_from:
                db.close(); messagebox.showerror("Error", "From account not found"); return
            from_name, from_status, from_pin, from_bal = row_from
            if from_status != "Active":
                db.close(); messagebox.showerror("Error", "From account is blocked"); return
            if from_name.strip().lower() != name.strip().lower():
                db.close(); messagebox.showerror("Error", "Name does not match from account"); return
            if from_pin != pin:
                db.close(); messagebox.showerror("Error", "Incorrect PIN for from account"); return
            if float(from_bal) < float(amt):
                db.close(); messagebox.showerror("Error", "Insufficient balance in from account"); return

            cur.execute("""
                SELECT cust_name, status
                FROM accounts
                WHERE account_no=%s
            """, (acc_to,))
            row_to = cur.fetchone()
            if not row_to:
                db.close(); messagebox.showerror("Error", "To account not found"); return
            to_name, to_status = row_to
            if to_status != "Active":
                db.close(); messagebox.showerror("Error", "To account is blocked"); return

            amt_s = sanitize_amount(amt)
            cur.execute("UPDATE accounts SET balance = balance - %s WHERE account_no=%s", (amt_s, acc_from))
            cur.execute("UPDATE accounts SET balance = balance + %s WHERE account_no=%s", (amt_s, acc_to))
            cur.execute("INSERT INTO transactions(account_no, cust_name, txn_type, amount) VALUES (%s,%s,%s,%s)",
                        (acc_from, from_name, "Transfer Out", amt_s))
            cur.execute("INSERT INTO transactions(account_no, cust_name, txn_type, amount) VALUES (%s,%s,%s,%s)",
                        (acc_to, to_name, "Transfer In", amt_s))

            db.commit(); db.close()
            messagebox.showinfo("Success", f"Transferred ₹{amt_s} to {acc_to}")
            self.tr_amt.delete(0,'end')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==================== Change PIN ====================
    def create_pin_change(self):
        name = "pin_change"
        self._set_title(name, "Change PIN")
        right = self.right_panels[name]
        form = tk.Frame(right, bg=self.colors["panel"]); form.pack(fill="both", expand=True, padx=20, pady=5)

        def add_row(label):
            tk.Label(form, text=label, bg=self.colors["panel"], fg=self.colors["text_muted"],
                     font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 2))

        add_row("Account Number")
        self.pc_acc = ttk.Entry(form, style="Dark.TEntry"); self.pc_acc.pack(fill="x")

        add_row("Old PIN")
        self.pc_old = ttk.Entry(form, style="Dark.TEntry", show="*"); self.pc_old.pack(fill="x")

        add_row("New PIN (min 4 digits)")
        self.pc_new = ttk.Entry(form, style="Dark.TEntry", show="*"); self.pc_new.pack(fill="x")

        add_row("Confirm New PIN")
        self.pc_conf = ttk.Entry(form, style="Dark.TEntry", show="*"); self.pc_conf.pack(fill="x")

        bottom_row = tk.Frame(right, bg=self.colors["panel"]); bottom_row.pack(fill="x", padx=20, pady=8)
        ttk.Button(bottom_row, text="Change PIN", style="Secondary.TButton", command=self.change_pin).pack(side="left", expand=True, fill="x", padx=(0,6))
        ttk.Button(bottom_row, text="Back", style="Secondary.TButton", command=lambda: self.show_frame("cust_dash")).pack(side="left", expand=True, fill="x", padx=(6,0))

    def change_pin(self):
        acc = self.pc_acc.get().strip()
        old = self.pc_old.get().strip()
        new = self.pc_new.get().strip()
        conf = self.pc_conf.get().strip()

        if not all([acc, old, new, conf]):
            messagebox.showerror("Error", "Fill all fields"); return
        if new != conf:
            messagebox.showerror("Error", "New PIN and confirmation do not match"); return
        if len(new) < 4 or not new.isdigit():
            messagebox.showerror("Error", "New PIN must be at least 4 digits"); return

        try:
            db = connect_db(); cur = db.cursor()
            cur.execute("SELECT pin, status FROM accounts WHERE account_no=%s", (acc,))
            row = cur.fetchone()
            if not row:
                db.close(); messagebox.showerror("Error", "Account not found"); return
            real_pin, status = row
            if status != "Active":
                db.close(); messagebox.showerror("Error", "Account is blocked"); return
            if real_pin != old:
                db.close(); messagebox.showerror("Error", "Old PIN is incorrect"); return

            cur.execute("UPDATE accounts SET pin=%s WHERE account_no=%s", (new, acc))
            db.commit(); db.close()
            messagebox.showinfo("Success", "PIN changed successfully")
            self.pc_old.delete(0,'end'); self.pc_new.delete(0,'end'); self.pc_conf.delete(0,'end')
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ==================== Run Application ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = BankApp(root)
    root.mainloop()

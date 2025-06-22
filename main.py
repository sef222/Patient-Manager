import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import csv
from datetime import datetime
from cryptography.fernet import Fernet
import sys
import bisect
import sv_ttk
import darkdetect
import pywinstyles
import sys; print(sys.executable)
import ctypes
import ctypes.wintypes
import sv_ttk
import pywinstyles
import darkdetect

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

ICON_PATH = os.path.join(BASE_DIR, "assets/icon.ico")

def go_to_patient_view(name):
    # Switch to View tab
    tabs.select(view_tab)

    # Find patient in TreeView
    for item in tree.get_children():
        if tree.item(item, 'values')[0] == name:
            tree.selection_set(item)
            tree.see(item)
            show_patient_info(name)
            break



def apply_blur_effect(hwnd):
    accent_policy = ctypes.Structure
    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [
            ("AccentState", ctypes.c_int),
            ("AccentFlags", ctypes.c_int),
            ("GradientColor", ctypes.c_int),
            ("AnimationId", ctypes.c_int)
        ]
    class WINCOMPATTRDATA(ctypes.Structure):
        _fields_ = [
            ("Attribute", ctypes.c_int),
            ("Data", ctypes.POINTER(ACCENTPOLICY)),
            ("SizeOfData", ctypes.c_size_t)
        ]

    accent = ACCENTPOLICY()
    accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
    accent.GradientColor = 0xCCFFFFFF  # 0xAABBGGRR (CC = ~80% opacity white)
    
    data = WINCOMPATTRDATA()
    data.Attribute = 19  # WCA_ACCENT_POLICY
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = ctypes.sizeof(accent)

    set_window_composition_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
    set_window_composition_attribute(hwnd, ctypes.byref(data))




BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "patients_data.json")
PASS_FILE = os.path.join(BASE_DIR, "admin_pass.enc")
LOG_FILE = os.path.join(BASE_DIR, "access_log.txt")
UNDO_FILE = os.path.join(BASE_DIR, "patients_data_undo.json")
BACKUP_FILE = os.path.join(BASE_DIR, "patients_data_backup.json")
KEY_FILE = os.path.join(BASE_DIR, "secret.key")

patients_data = {}
user_mode = None

billing_info = {}

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    theme = sv_ttk.get_theme()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if theme == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if theme == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def on_visit_select(event):
    sel = visits_listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    visit = visits[idx]
    billing_info.clear()
    for widget in billing_tab.winfo_children():
        widget.destroy()

    ttk.Label(billing_tab, text=f"Visit: {visit['time']} - {visit['note']}").pack(pady=5)

    for key in ["total", "paid", "left"]:
        billing_info[key] = tk.StringVar(value=visit['billing'].get(key, ""))
        ttk.Label(billing_tab, text=key.capitalize() + ":").pack()
        ttk.Entry(billing_tab, textvariable=billing_info[key]).pack()

    def save_billing():
        for key in ["total", "paid", "left"]:
            visit['billing'][key] = billing_info[key].get()
        save_data()
        log_access(f"Updated billing for {name} visit: {visit['time']}")

    ttk.Button(billing_tab, text="Save Billing", command=save_billing).pack(pady=10)




def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)

def load_key():
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, 'rb') as f:
        return Fernet(f.read())

fernet = load_key()

def log_access(entry):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - {entry}\n")

def save_password(new_password):
    with open(PASS_FILE, 'wb') as f:
        f.write(fernet.encrypt(new_password.encode()))
    log_access("Admin password changed")

def load_password():
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, 'rb') as f:
            try:
                return fernet.decrypt(f.read()).decode()
            except:
                return "admin123"
    else:
        return "admin123"

admin_password = load_password()

def login():
    global user_mode
    root = tk.Tk()
    root.iconbitmap(ICON_PATH)

    root.withdraw()
    answer = messagebox.askquestion("Login", "Login as Admin?", parent=root)
    if answer == 'yes':
        pwd = simpledialog.askstring("Admin Password", "Enter password:", show='*', parent=root)
        root.destroy()
        if pwd == admin_password:
            user_mode = "admin"
            log_access("Admin logged in")
            return True
        else:
            messagebox.showerror("Access Denied", "Incorrect password")
            return False
    else:
        root.destroy()
        user_mode = "assistant"
        log_access("Assistant logged in")
        return True

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for p in data.values():
                p['visits'] = sorted(p.get('visits', []))
            return data
    return {}

def save_data():
    with open(BACKUP_FILE, 'w', encoding='utf-8') as bf:
        json.dump(patients_data, bf)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(patients_data, f)
    with open(UNDO_FILE, 'w', encoding='utf-8') as f:
        json.dump(patients_data, f)

def undo_changes():
    global patients_data
    if os.path.exists(UNDO_FILE):
        with open(UNDO_FILE, 'r', encoding='utf-8') as f:
            patients_data = json.load(f)
            for p in patients_data.values():
                p['visits'] = sorted(p.get('visits', []))
            refresh_view()
            refresh_search()
            clear_patient_info()
            messagebox.showinfo("Undo", "Changes reverted to last save.")
            log_access("Undo applied")

def export_csv():
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[["CSV files", "*.csv"]])
    if path:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Folder", "Mobile", "Visit Time", "Note", "Total", "Paid", "Left"])
            for name, data in patients_data.items():
                visits = data.get('visits', [])
                bills = data.get('bills', {})
                if not visits:
                    writer.writerow([name, data['folder'], data['mobile'], "", "", "", "", ""])
                for visit in visits:
                    if ' - ' in visit:
                        time, note = visit.split(' - ', 1)
                    else:
                        time, note = visit, ""
                    bill = bills.get(visit, {"total": "", "paid": "", "left": ""})
                    writer.writerow([
                        name, data['folder'], data['mobile'],
                        time, note,
                        bill.get('total', ''), bill.get('paid', ''), bill.get('left', '')
                    ])
        messagebox.showinfo("Export", "Data exported successfully")
        log_access("Data exported to CSV")

def import_csv():
    if user_mode != 'admin':
        messagebox.showerror("Permission Denied", "Admin access required")
        return
    path = filedialog.askopenfilename(filetypes=[["CSV files", "*.csv"]])
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['Name'].strip()
                folder = row['Folder'].strip()
                mobile = row['Mobile'].strip()
                if name:
                    patients_data[name] = {"folder": folder, "mobile": mobile, "visits": []}
        save_data()
        refresh_view()
        refresh_search()
        messagebox.showinfo("Import", "Data imported successfully")
        log_access("Data imported from CSV")

def change_password():
    global admin_password
    new_pass = simpledialog.askstring("Change Password", "Enter new admin password:", show='*')
    if new_pass:
        save_password(new_pass)
        admin_password = new_pass
        messagebox.showinfo("Success", "Password changed")

def view_logs():
    win = tk.Toplevel(app)
    win.iconbitmap(ICON_PATH)

    win = tk.Toplevel(app)
    win.title("Logs")
    text = tk.Text(win)
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            text.insert('1.0', f.read())
    except:
        text.insert('1.0', "No logs found.")
    text.pack(expand=True, fill='both')

def clear_logs():
    open(LOG_FILE, 'w', encoding='utf-8').close()
    messagebox.showinfo("Cleared", "Logs cleared.")
    log_access("Logs cleared")

def open_settings():
    win = tk.Toplevel(app)
    win.iconbitmap(ICON_PATH)

    settings = tk.Toplevel(app)
    settings.title("Settings")
    settings.geometry("400x300")
    ttk.Label(settings, text="Settings", font=("Segoe UI", 14)).pack(pady=10)
    if user_mode == "admin":
        ttk.Button(settings, text="Change Password", command=change_password).pack(pady=5)
        ttk.Button(settings, text="View Logs", command=view_logs).pack(pady=5)
        ttk.Button(settings, text="Undo Changes", command=undo_changes).pack(pady=5)
        ttk.Button(settings, text="Clear Logs", command=clear_logs).pack(pady=5)

def add_patient():
    name = name_var.get().strip()
    fnum = fnum_var.get().strip()
    mobile = mob_var.get().strip()
    if not name:
        messagebox.showerror("Invalid", "Name cannot be empty")
        return
    if name in patients_data:
        messagebox.showerror("Duplicate", "Patient already exists")
        return
    patients_data[name] = {"folder": fnum, "mobile": mobile, "visits": []}
    save_data()
    refresh_view()
    log_access(f"Added patient: {name}")
    name_var.set("")
    fnum_var.set("")
    mob_var.set("")

def refresh_view():
    tree.delete(*tree.get_children())
    sorted_names = sorted(patients_data.keys())
    for name in sorted_names:
        data = patients_data[name]
        tree.insert('', 'end', values=(name, data['folder'], data['mobile']))
    clear_patient_info()
    edit_btn.config(state='disabled')
    delete_btn.config(state='disabled')

def on_tree_select(event):
    selected = tree.selection()
    if selected:
        edit_btn.config(state='normal')
        delete_btn.config(state='normal')
        patient_name = tree.item(selected[0], 'values')[0]
        show_patient_info(patient_name)
    else:
        edit_btn.config(state='disabled')
        delete_btn.config(state='disabled')
        clear_patient_info()

def edit_patient(name):
    win = tk.Toplevel(app)
    win.iconbitmap(ICON_PATH)

    data = patients_data.get(name)
    if not data:
        messagebox.showerror("Error", "Patient not found")
        return
    edit_win = tk.Toplevel(app)
    edit_win.title(f"Edit Patient - {name}")
    edit_win.geometry("300x300")

    name_var_edit = tk.StringVar(value=name)
    folder_var_edit = tk.StringVar(value=data['folder'])
    mobile_var_edit = tk.StringVar(value=data['mobile'])

    ttk.Label(edit_win, text="Name:").pack(pady=5)
    entry_name = ttk.Entry(edit_win, textvariable=name_var_edit)
    entry_name.pack()

    ttk.Label(edit_win, text="Folder #:").pack(pady=5)
    entry_folder = ttk.Entry(edit_win, textvariable=folder_var_edit)
    entry_folder.pack()

    ttk.Label(edit_win, text="Mobile #:").pack(pady=5)
    entry_mobile = ttk.Entry(edit_win, textvariable=mobile_var_edit)
    entry_mobile.pack()

    def save_edit():
        new_name = name_var_edit.get().strip()
        new_folder = folder_var_edit.get().strip()
        new_mobile = mobile_var_edit.get().strip()
        if not new_name:
            messagebox.showerror("Invalid", "Name cannot be empty")
            return
        if new_name != name and new_name in patients_data:
            messagebox.showerror("Duplicate", "Patient name already exists")
            return
        visits = patients_data[name].get("visits", [])
        if new_name != name:
            patients_data.pop(name)
        patients_data[new_name] = {"folder": new_folder, "mobile": new_mobile, "visits": visits}
        save_data()
        refresh_view()
        refresh_search()
        log_access(f"Edited patient: {name} -> {new_name}")
        edit_win.destroy()

    ttk.Button(edit_win, text="Save", command=save_edit).pack(pady=10)

def delete_patient(name):
    if messagebox.askyesno("Confirm Delete", f"Delete patient '{name}'?"):
        patients_data.pop(name, None)
        save_data()
        refresh_view()
        refresh_search()
        clear_patient_info()
        log_access(f"Deleted patient: {name}")

def on_edit_button():
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0], 'values')
        edit_patient(values[0])

def on_delete_button():
    selected = tree.selection()
    if selected:
        values = tree.item(selected[0], 'values')
        delete_patient(values[0])

def clear_patient_info():
    for widget in patient_info_frame.winfo_children():
        widget.destroy()

def show_patient_info(name):
    clear_patient_info()
    data = patients_data.get(name)
    if not data:
        return

    ttk.Label(patient_info_frame, text=f"Name: {name}", font=("Segoe UI", 12, "bold")).pack(anchor='w')
    ttk.Label(patient_info_frame, text=f"Folder #: {data['folder']}").pack(anchor='w')
    ttk.Label(patient_info_frame, text=f"Mobile #: {data['mobile']}").pack(anchor='w')

    ttk.Separator(patient_info_frame, orient='horizontal').pack(fill='x', pady=5)

    notebook = ttk.Notebook(patient_info_frame)
    notebook.pack(fill='both', expand=True)

    visits_tab = ttk.Frame(notebook)
    billing_tab = ttk.Frame(notebook)

    notebook.add(visits_tab, text="Visits")
    notebook.add(billing_tab, text="Billing")

    visits = data.setdefault('visits', [])
    bills = data.setdefault('bills', {})

    visits_listbox = tk.Listbox(visits_tab, height=6)
    visits_listbox.pack(fill='x', pady=5, expand=True)

    for visit in visits:
        visits_listbox.insert('end', visit)

    def on_visit_select(event):
        selected = visits_listbox.curselection()
        if not selected:
            return
        visit_text = visits[selected[0]]
        bill = bills.get(visit_text, {"total": "", "paid": "", "left": ""})

        for widget in billing_tab.winfo_children():
            widget.destroy()

        ttk.Label(billing_tab, text=f"Visit: {visit_text}", font=("Segoe UI", 10, "bold")).pack(pady=5)
        total_var = tk.StringVar(value=bill["total"])
        paid_var = tk.StringVar(value=bill["paid"])
        left_var = tk.StringVar()


        ttk.Label(billing_tab, text="Total:").pack()
        ttk.Entry(billing_tab, textvariable=total_var).pack()
        ttk.Label(billing_tab, text="Paid:").pack()
        ttk.Entry(billing_tab, textvariable=paid_var).pack()
        ttk.Label(billing_tab, text="Left to Pay:").pack()
        ttk.Entry(billing_tab, textvariable=left_var).pack()

        def save_bill():
            try:
                total = float(total_var.get())
                paid = float(paid_var.get())
                left = total - paid
                left_var.set(str(left))
                bills[visit_text] = {
                    "total": str(total),
                    "paid": str(paid),
                    "left": str(left)
                }
                data['bills'] = bills
                save_data()
                log_access(f"Updated bill for {name}: {visit_text}")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for Total and Paid.")


        ttk.Button(billing_tab, text="Save", command=save_bill).pack(pady=10)

    visits_listbox.bind("<<ListboxSelect>>", on_visit_select)

    def add_visit():
        new_note = simpledialog.askstring("Add Visit", "Enter visit note:")
        if new_note:
            full = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - {new_note}"
            idx = bisect.bisect_left(visits, full)
            if idx == len(visits) or visits[idx] != full:
                visits.insert(idx, full)
                visits_listbox.insert(idx, full)
                data['visits'] = visits
                save_data()
                log_access(f"Added visit to {name}: {new_note}")

    def delete_visit():
        sel = visits_listbox.curselection()
        if sel:
            idx = sel[0]
            visit_text = visits.pop(idx)
            data['visits'] = visits
            bills.pop(visit_text, None)
            data['bills'] = bills
            visits_listbox.delete(idx)
            save_data()
            log_access(f"Deleted visit from {name}: {visit_text}")

    btns = ttk.Frame(visits_tab)
    btns.pack(pady=5)
    ttk.Button(btns, text="Add Visit", command=add_visit).pack(side='left', padx=5)
    ttk.Button(btns, text="Delete Visit", command=delete_visit).pack(side='left', padx=5)

def refresh_search_results(results):
    for widget in search_results.winfo_children():
        widget.destroy()
    for name, data in results:
        frame = tk.Frame(search_results, bd=2, relief="ridge", padx=10, pady=5, bg="white")
        frame.pack(padx=0, pady=5, fill='x', expand=True)

        # Patient summary
        name_label = tk.Label(frame, text=name, font=("Segoe UI", 12, "bold"), bg="white", fg="blue", cursor="hand2")
        name_label.pack(anchor='w')
        name_label.bind("<Button-1>", lambda e, n=name: go_to_patient_view(n))

        tk.Label(frame, text=f"Folder #: {data['folder']}, Mobile #: {data['mobile']}", bg="white").pack(anchor='w')

        # Collapsible visits section
        visits = data.get("visits", [])
        bills = data.get("bills", {})

        if visits:
            # Toggle logic
            collapsed = tk.BooleanVar(value=True)
            toggle_btn = ttk.Button(frame, text="► Show Visits", style="TButton")
            toggle_btn.pack(anchor='w', pady=5)

            visits_frame = tk.Frame(frame, bg="white")
            visits_frame.pack(anchor='w', fill='x', padx=10)
            visits_frame.pack_forget()  # Start hidden

            def toggle():
                if collapsed.get():
                    visits_frame.pack(anchor='w', fill='x', padx=10)
                    toggle_btn.config(text="▼ Hide Visits")
                else:
                    visits_frame.pack_forget()
                    toggle_btn.config(text="► Show Visits")
                collapsed.set(not collapsed.get())

            toggle_btn.config(command=toggle)

            for visit in visits:
                tk.Label(visits_frame, text=f"• {visit}", anchor='w', bg="white").pack(fill='x')
                bill = bills.get(visit, {})
                if bill:
                    bill_str = f"    → Total: {bill.get('total', '')}, Paid: {bill.get('paid', '')}, Left: {bill.get('left', '')}"
                    tk.Label(visits_frame, text=bill_str, fg="gray", anchor='w', bg="white").pack(fill='x')

        # Buttons
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(anchor='e', pady=5)
        ttk.Button(btn_frame, text="Edit", command=lambda n=name: edit_patient(n)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Delete", command=lambda n=name: delete_patient(n)).pack(side='left', padx=5)

def prefix_search(query_lower):
    keys = sorted(patients_data.keys())
    left = bisect.bisect_left(keys, query_lower)
    results = []
    for i in range(left, len(keys)):
        key_lower = keys[i].lower()
        if key_lower.startswith(query_lower):
            results.append((keys[i], patients_data[keys[i]]))
        else:
            break
    return results

def search():
    query = search_var.get().strip().lower()
    for widget in search_results.winfo_children():
        widget.destroy()
    if not query:
        progress_bar.pack_forget()
        return

    progress_bar.pack(fill='x', padx=10, pady=5)
    progress_var.set(0)
    search_results.update()

    all_items = list(patients_data.items())
    total = len(all_items)
    idx = 0
    results = []
    chunk_size = 50

    def process_chunk():
        nonlocal idx
        count = 0
        while count < chunk_size and idx < total:
            name, data = all_items[idx]
            if (query in name.lower() or
                query in data['folder'].lower() or
                query in data['mobile'].lower()):
                results.append((name, data))
            idx += 1
            count += 1
        progress_var.set((idx / total) * 100)
        search_results.update()
        if idx < total:
            app.after(10, process_chunk)
        else:
            progress_bar.pack_forget()
            refresh_search_results(results)

    process_chunk()



if __name__ == "__main__":
    if not login():
        sys.exit()

    patients_data = load_data()

    app = tk.Tk()
    hwnd = ctypes.windll.user32.GetParent(app.winfo_id())
    apply_blur_effect(hwnd)



    app.title("Patient Manager")
    app.geometry("1280x720")

    sv_ttk.set_theme("light")
 # Auto dark/light
    apply_theme_to_titlebar(app)


    toolbar = tk.Frame(app, bg="lightgray")
    toolbar.pack(side='top', fill='x')

    ttk.Button(toolbar, text="⚙ Settings", command=open_settings).pack(side='right', padx=10, pady=5)
    ttk.Button(toolbar, text="📤 Export CSV", command=export_csv).pack(side='right', padx=10, pady=5)
    ttk.Button(toolbar, text="📥 Import CSV", command=import_csv).pack(side='right', padx=10, pady=5)
    app.iconbitmap("assets/icon.ico")

    tabs = ttk.Notebook(app)
    tabs.pack(expand=True, fill='both')

    add_tab = ttk.Frame(tabs)
    view_tab = ttk.Frame(tabs)
    search_tab = ttk.Frame(tabs)

    tabs.add(add_tab, text='Add Patient')
    tabs.add(view_tab, text='View Patients')
    tabs.add(search_tab, text='Search')

    # Add Patient tab UI
    name_var = tk.StringVar()
    fnum_var = tk.StringVar()
    mob_var = tk.StringVar()

    for label, var in zip(["Name", "Folder #", "Mobile #"], [name_var, fnum_var, mob_var]):
        ttk.Label(add_tab, text=label).pack(pady=3)
        ttk.Entry(add_tab, textvariable=var).pack(pady=3)

    ttk.Button(add_tab, text="Add Patient", command=add_patient).pack(pady=10)

    # View Patients tab setup
    patient_info_frame = ttk.Frame(view_tab, relief='ridge', padding=10)
    patient_info_frame.pack(fill='x', padx=5, pady=5)

    tree = ttk.Treeview(view_tab, columns=("Name", "Folder", "Mobile"), show='headings')
    tree.heading("Name", text="Name")
    tree.heading("Folder", text="Folder #")
    tree.heading("Mobile", text="Mobile #")
    tree.column("Name", width=200)
    tree.column("Folder", width=150)
    tree.column("Mobile", width=150)
    tree.pack(side="left", fill="both", expand=True, padx=(5,0), pady=5)

    scrollbar = ttk.Scrollbar(view_tab, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="left", fill="y", pady=5)

    btn_frame_view = tk.Frame(view_tab)
    btn_frame_view.pack(side="bottom", fill='x', pady=5)

    edit_btn = ttk.Button(btn_frame_view, text="Edit Selected", command=on_edit_button, state='disabled')
    edit_btn.pack(side='left', padx=5)
    delete_btn = ttk.Button(btn_frame_view, text="Delete Selected", command=on_delete_button, state='disabled')
    delete_btn.pack(side='left', padx=5)

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # Search tab setup


    # Search tab setup
    search_var = tk.StringVar()
    ttk.Label(search_tab, text="Enter search query:").pack(pady=5)
    search_entry = ttk.Entry(search_tab, textvariable=search_var)
    search_entry.pack(pady=5)

    search_btn = ttk.Button(search_tab, text="Search", command=search)
    search_btn.pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(search_tab, variable=progress_var, maximum=100)
    progress_bar.pack(side="bottom", fill="x", pady=5)


    # Scrollable search results area
    search_canvas = tk.Canvas(search_tab)
    scrollbar = ttk.Scrollbar(search_tab, orient="vertical", command=search_canvas.yview)
    scrollable_frame = tk.Frame(search_canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: search_canvas.configure(
            scrollregion=search_canvas.bbox("all")
        )
    )

    search_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    search_canvas.configure(yscrollcommand=scrollbar.set)

    search_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    search_results = scrollable_frame


    refresh_view()
    app.mainloop()

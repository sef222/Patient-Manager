# Patient-Manager
An app to manage dental/everything else patients easily

# 🦷 Patient Manager Desktop App

A modern, offline dental clinic management system built with Python and Tkinter.  
It supports patient records, visit history, billing, CSV import/export, search, logs, and admin settings — all with a clean, Windows 11-style UI.

---

## ✨ Features

- ✅ Add, edit, delete patients
- ✅ Visit notes + automatic timestamps
- ✅ Billing system (total / paid / remaining)
- ✅ CSV import/export support
- ✅ Admin login with encrypted password
- ✅ Undo system & logs
- ✅ Real-time search with loading bar
- ✅ Modern UI: sv-ttk + blur effects + emoji
- ✅ Works offline, built in pure Python

---

## 📦 Installation

1. **Install Python 3.10+**  
   [Download Python](https://www.python.org/downloads/)

2. **Install required libraries:**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install sv-ttk pywinstyles darkdetect cryptography
   ```

3. **Run the app:**
   ```bash
   python main.py
   ```

---

## 🖼️ Customization

- **Change icon:** replace `assets/icon.ico`
- **Switch theme:** edit `sv_ttk.set_theme("light")` or use `darkdetect`
- **App title:** edit `app.title("🦷 Patient Manager")`

---

## 🔐 Admin Login

- **Default admin password:** `admin123`
- You’ll be prompted on launch to choose Assistant or Admin mode.
- Admins can change the password, undo changes, view logs, and import data.

---

## 💾 Data Storage

- All patient data is stored in `patients_data.json` in the same folder.
- Encrypted password is stored in `admin_pass.enc`.

---

## 📁 File Structure

```
📦 your_project_folder
 ┣ 📁 assets/
 ┃ ┗ 🖼️ icon.ico
 ┣ 📄 main.py
 ┣ 📄 patients_data.json
 ┣ 📄 secret.key
 ┣ 📄 admin_pass.enc
 ┣ 📄 access_log.txt
 ┣ 📄 requirements.txt
```

---

## 📦 Packaging as .EXE (Optional)

You can use [PyInstaller](https://www.pyinstaller.org/) to convert to `.exe`:
```bash
pyinstaller --noconsole --onefile --icon=assets/icon.ico main.py
```

---

## 🧑‍💻 Author

Made by Seif Safina  
Powered by `tkinter`, `sv-ttk`.
---

## 🪪 License

MIT License. Use freely and modify responsibly.

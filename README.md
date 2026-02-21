# RDV Medical (Tkinter + SQLite)

A simple appointment booking system built with **Python (Tkinter)** and **SQLite**.
It includes 3 roles: **Admin**, **Doctor (Médecin)**, and **Patient**.

## Features

### Authentication
- Login system for Admin / Doctor / Patient
- Passwords stored securely using **hashing**
- Patient registration (create account)

### Admin (Espace Admin)
- Add a doctor (username, password, email, speciality)
- Activate / deactivate doctors (inactive doctors are hidden from patients)
- Speciality search to speed up doctor creation (Combobox filtering)

### Doctor (Espace Médecin)
- Create appointment slots (day or week)
- Presets: Morning / Afternoon / Custom
- Prevent creating slots in past dates
- Agenda view separated into:
  - **Free slots (Libres)**: can delete future free slots
  - **Booked slots (Réservés)**: shows patient name

### Patient (Espace Patient)
- Book appointment with a doctor
- Filter doctors by speciality
- Calendar date selection (past days disabled)
- Slots list (past hours disabled on today)
- Urgent appointment option (requires a reason)
- Manage appointments (view / cancel / modify)
- Reminder:
  - Reminder card for appointments within 48h
  - Popup reminder when opening the patient home

## Tech Stack
- Python 3
- Tkinter (GUI)
- SQLite (Database)

## Project Structure (example)
- `services/` : business logic (auth, admin, rdv)
- `ui/` : Tkinter windows
- `data/` : database access

## Future Improvements
- Email-based reminder notifications
- Calendar-style visual agenda (monthly/weekly grid view)
- Statistics dashboard (appointments per doctor, per month)
- Search & filtering improvements in admin panel
- Improved UI responsiveness (dynamic resizing)

## How to Run
1. Install Python 3
2. Run the application (example):
   ```bash
   python main.py
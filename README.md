RDV Medical (Tkinter + SQLite)

A desktop medical appointment management system built with Python (Tkinter) and SQLite.
It manages scheduling workflows between Admin, Doctor (Médecin), and Patient using a modular layered architecture.

The system separates:

User Interface (Tkinter)

Business Logic (Services layer)

Data Access Layer (SQLite)

This layered design ensures maintainability, modularity, and clear separation of responsibilities.

Features
Authentication

Secure login for Admin / Doctor / Patient

Passwords stored using SHA-256 hashing (no plaintext storage)

Patient self-registration

Role-based access control

Admin (Espace Admin)

Create doctor accounts

Assign speciality

Activate / deactivate doctors

Dynamic speciality filtering (Combobox)

Soft deactivation (historical data preserved)

Doctor (Espace Médecin)

Create appointment slots (daily / weekly)

Presets: Morning / Afternoon / Custom

Prevent creating slots in past dates

Agenda view:

Free slots (Libres) → delete future free slots

Reserved slots (Réservés) → display patient details

Urgent appointment visualization

Automatic filtering of upcoming appointments

Patient (Espace Patient)

Browse doctors (with speciality filter)

Interactive calendar (past dates disabled)

Time filtering (past hours disabled for current day)

Book standard or urgent appointments

Urgent booking requires justification

Manage appointments (view / cancel / modify)

Reminder system:

Popup alert on login (within 48h)

Persistent visual reminder banner

Tech Stack

Python 3

Tkinter (GUI Framework)

SQLite3 (Embedded Database)

Project Structure

ui/ → Tkinter interface

services/ → Business logic (Auth, RDV, Admin)

data/ → Database layer

figures/ → UML diagrams

screenshots/ → Documentation images

Database

SQLite relational schema includes:

users

creneaux (appointment slots)

rdv (appointments)

Relationships

One doctor → multiple slots

One slot → zero or one appointment

One patient → multiple appointments

UML Diagram

Screenshots
Main Menu

Doctor Agenda – Free Slots

Doctor Agenda – Urgent Appointment

Patient Reminder Popup

Patient Reminder Banner

Admin Panel

Patient Booking

▶ How to Run

Install Python 3

Navigate to the project folder

Run:

python main.py

The login window will appear automatically.

🔐 Demo Credentials (For Evaluation)

Pre-configured accounts are provided for academic evaluation:

Administrator

Username: admin

Password: admin

Doctor

Username: dranita

Password: anita

Patient

Username: patient1

Password: 1234

🧪 Suggested Evaluation Flow

To test the system:

Login as Admin

Create or deactivate a doctor

Login as Doctor

Create appointment slots

Login as Patient

Book a standard appointment

Book an urgent appointment (motif required)

Verify:

Double booking prevention

48h reminder popup

Role-based access separation

Future Improvements

Email notification service (SMTP integration)

SMS notification system

Monthly calendar grid view

Statistical dashboard (appointments per doctor / month)

REST API version (Flask / FastAPI backend)

Stronger password security (salting + authentication hardening)
# MedicAll - Hospital Management System

MedicAll is a web-based Hospital Management System (HMS) designed to streamline healthcare operations. It bridges the gap between hospital administration, doctors, and patients, offering a seamless experience for appointment booking, medical history tracking, and doctor schedule management.

Built with simplicity and efficiency in mind using **Flask** and **Bootstrap**.

---

## 🚀 Features

### For Administrators
- **Dashboard Overview**: Get real-time insights into total doctors, patients, and appointment stats.
- **Doctor Management**: Onboard new specialists, update profiles, or remove staff.
- **Patient Management**: View registered patients and manage access.
- **Schedule Control**: Oversee appointment flows and handle cancellations if necessary.

### For Doctors
- **Personalized Dashboard**: View upcoming appointments at a glance.
- **Patient History**: Access detailed treatment history for informed diagnoses.
- **Treatment Records**: Digital prescriptions and diagnosis logging.
- **Availability Manager**: Set working hours and days off to prevent scheduling conflicts.

### For Patients
- **Easy Booking**: Search doctors by specialization and book available slots.
- **Medical History**: Access past diagnoses and prescriptions anytime.
- **Profile Management**: Keep personal contact details up to date.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Jinja2
- **Visualization**: Chart.js for data analytics

---

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/22f3003138/MedicAll.git
cd MedicAll
```

### 2. Set Up Virtual Environment
It's recommended to use a virtual environment to manage dependencies.

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the root directory. You can use the example below:

```env
FLASK_APP=app.py
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URI=sqlite:///hms.db
```

### 5. Initialize & Seed Database
The project comes with a migration script to set up the database and populate it with sample data (doctors, patients, appointments).

```bash
python migrations/migration.py
```
*This will create `hms.db` in the `instance/` folder and fill it with realistic test data.*

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to: `http://127.0.0.1:5000`

---

## 🔐 Test Credentials

You can use these accounts to explore the different roles in the system immediately after seeding.

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@hospital.com` | `admin123` |
| **Doctor** | `rajesh.k@hospital.com` | `doctor123` |
| **Patient** | `rohan.m@example.com` | `patient123` |

---

## 📂 Project Structure

```
MedicAll/
├── app.py                  # Entry point
├── models/                 # Database schema definitions
├── routes/                 # URL routing & controller logic
│   ├── admin.py
│   ├── doctor.py
│   ├── patient.py
│   └── ...
├── templates/              # HTML templates (Jinja2)
├── static/                 # CSS, JS, Images
├── migrations/             # Database seeding scripts
└── instance/               # SQLite database storage
```

---
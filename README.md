# Campus Event Management System (CEMS)

A web-based campus event management system built with Django and MySQL, featuring a KNN-based event recommendation engine.

---

## Project Overview

CEMS allows students to browse, register for, and give feedback on campus events. An admin can create, edit, and delete events. The system uses the K-Nearest Neighbours (KNN) algorithm to recommend personalised events to students based on their registration and feedback history.

---

## Features

- Student registration and login
- Browse and search events by title or category
- Event registration with capacity checking
- Registration cancellation
- Event feedback with star ratings
- KNN-based personalised event recommendations
- Admin dashboard with event statistics
- Admin event creation, editing, and deletion
- Role-based access control (student / admin)

---

## Technologies Used

| Technology     | Purpose                          |
|----------------|----------------------------------|
| Python 3.13    | Backend language                 |
| Django 4.2     | Web framework                    |
| MySQL          | Database                         |
| scikit-learn   | KNN recommendation engine        |
| pandas/numpy   | Data processing for KNN          |
| Bootstrap 5    | Frontend UI                      |
| HTML/CSS/JS    | Templates and styling            |

---

## Database Setup

1. Open MySQL Workbench and run:

```sql
CREATE DATABASE cems_db;
CREATE USER 'cems_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON cems_db.* TO 'cems_user'@'localhost';
GRANT ALL PRIVILEGES ON test_cems_db.* TO 'cems_user'@'localhost';
FLUSH PRIVILEGES;
```

2. Update `cems/settings.py` with your MySQL password:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cems_db',
        'USER': 'cems_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## How to Run

1. Clone or extract the project folder.

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (admin account):

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

7. Open your browser and go to: `http://127.0.0.1:8000`

---

## Running Tests

```bash
python manage.py test events
python manage.py test accounts
```

---

## Test Accounts

| Role    | Username | Password     |
|---------|----------|--------------|
| Admin   | admin    | (set during createsuperuser) |
| Student | (register via the website) | — |

---

## Notes

- This project is configured for **development use only**.
- In a production environment, `SECRET_KEY` and database credentials should be stored in environment variables, and `DEBUG` should be set to `False`.
- The timezone is set to `Europe/London` to reflect the UK university context.

---

## Module

LD6053 — Undergraduate Project  
Northumbria University
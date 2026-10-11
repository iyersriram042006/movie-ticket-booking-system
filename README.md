# Movie Ticket Booking System (CineBook)

A web-based Movie Ticket Booking System developed as an individual Project-Based Learning (PBL) activity. The project is managed using Scrum in JIRA (project key: MTB) and implements two modules with complete testing.

## Modules Implemented

1. **User Registration & Login**: account creation with input validation, secure password storage, login and logout.
2. **Seat Selection & Booking**: movie and show selection, seat layout, seat booking with validation and booking confirmation.

## Tech Stack

- Python 3, Flask
- SQLite
- HTML, CSS (Jinja2 templates)

## Project Structure

```
MTB_Project/
├── app.py            # Flask routes
├── database.py       # Database connection and queries
├── validators.py     # Input validation functions
├── templates/        # HTML templates
├── static/           # CSS
├── tests/            # Test cases and test scripts
└── requirements.txt
```

## How to Run

```bash
git clone <repository-url>
cd <repository-folder>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5001/register in the browser.

## Project Management

Managed in JIRA with epics, user stories, sub-tasks, sprint planning, defect tracking and sprint reports.

## Author

Sriram Iyer, B.Tech CSE, Ramdeobaba University, Nagpur
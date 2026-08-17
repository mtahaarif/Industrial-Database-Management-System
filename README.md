# Industrial Database Management System

A web-based database management system built for **Universal Metals**, a wire and cable manufacturing company. The project pairs a normalized SQL Server database (designed via an EER diagram) with a Flask web application that gives non-technical staff a simple, form-driven interface for day-to-day CRUD operations — without needing to write SQL.

This was built as a Database Engineering project for the 6th Semester of a Bachelor of Computer Engineering program.

## Overview

Manufacturing operations at Universal Metals involve several interrelated entities — employees, factories, maintenance records, suppliers/parties, raw and finished materials, and multiple production processes (enamel copper wire, wrapping, bare strip/wire, submersible copper wire, copper tape, aluminium enamel wire). The database models these as a normalized relational schema, and the app exposes:

- Generic table browsing and CRUD for core entity tables
- Dynamic creation/deletion of new tables at runtime
- Specialized "combined views" that join a parent table (`FACTORY_PRODUCTION`, `MATERIAL`) with its subtype tables, reflecting a supertype/subtype (category) design in the ER model
- A simple session-based login gate

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | Microsoft SQL Server |
| DB Driver | `pyodbc` (ODBC Driver 17 for SQL Server) |
| Frontend | Jinja2 templates, vanilla HTML/CSS/JS, Font Awesome icons |
| Auth | Flask session, hardcoded credentials |

## Project Structure

```
.
├── app.py                          # Flask application: routes, DB access, business logic
├── static/
│   └── picprojlogin.jpeg           # Login page background image
├── templates/
│   ├── login.html                  # Login screen
│   ├── dashboard.html              # Main landing page after login — lists all manageable tables
│   ├── table_view.html             # Generic table viewer with search/filter
│   ├── add_record.html             # Generic "insert row" form (auto-built from table columns)
│   ├── edit_record.html            # Generic "update row" form (select by primary key)
│   ├── delete_record.html          # Generic "delete row" form (select by primary key)
│   ├── add_table.html              # Dynamic table creation form
│   ├── factory_production.html     # Selector for factory production subtypes
│   ├── factory_combined_view.html  # Joined view: FACTORY_PRODUCTION + selected subtype table
│   ├── material_selector.html      # Selector for material subtypes
│   └── material_combined_view.html # Joined view: MATERIAL + selected subtype table
└── README.md
```

## Data Model

The schema follows a supertype/subtype (category) pattern for two key entities:

**Factory Production** — a `FACTORY_PRODUCTION` parent table linked via foreign key to one of several subtype tables, each representing a distinct product line:
- Enamel Copper Wire (`ENAMEL_COPPER_WIRE`)
- Wrapping Section (`WRAPPED_SECTION`)
- Bare Strip (`BARE_STRIP`)
- Bare Wire (`BARE_WIRE`)
- Submersible Copper Wire (`SUBMERSIBLE_COPPER_WIRE`)
- Copper Tape (`COPPER_BRIE`)
- Aluminium Enamel Wire (`ALUMINIUM_ENAMEL_WIRE`)

**Material** — a `MATERIAL` parent table linked to:
- Raw Material (`RAW_MATERIAL`)
- Finished Material (`FINISHED_MATERIAL`)

**Core standalone entities** (managed generically from the dashboard):
- `EMPLOYEE`
- `FACTORY`
- `MAINTENANCE`
- `PARTY`
- `WRAPPED_SECTION`

The app discovers primary keys, foreign keys, and column lists at runtime via SQL Server's `INFORMATION_SCHEMA` views, rather than hardcoding column definitions — this is what lets the generic add/edit/delete/table-creation forms work against any table.

## Features

- **Login-gated access** — all routes except `/` require an active session.
- **Dashboard** — card-based UI listing every manageable table plus dedicated cards for Factory Production and Materials, each with quick actions (View, Add, Edit, Delete Record, Delete Table).
- **Generic table viewer** — browse any table's rows with column-based search/filter (`?attribute=...&search_query=...`).
- **Generic record CRUD**:
  - *Add*: form fields generated from the target table's columns.
  - *Edit*: pick a record by primary key, choose an attribute, supply a new value.
  - *Delete*: pick a record by primary key to remove.
- **Dynamic schema management** — create new tables (with an auto-generated `id INT IDENTITY(1,1) PRIMARY KEY` plus user-defined `NVARCHAR(255)` columns) or drop existing ones directly from the UI.
- **Combined subtype views** — for Factory Production and Material categories, the app auto-detects the parent's primary key and the subtype's foreign key, then runs an inner join so users see the full picture (e.g. a wire's factory-production record alongside its enamel-copper-wire-specific attributes) in one table.
- **Flash messaging** — success/error feedback rendered as animated toast-style notifications.

## Application Routes

| Route | Methods | Purpose |
|---|---|---|
| `/` | GET, POST | Login |
| `/logout` | GET | Clear session and return to login |
| `/dashboard` | GET | Main table listing |
| `/table/<table_name>` | GET | View table rows, with optional search |
| `/table/<table_name>/add` | GET, POST | Insert a new record |
| `/table/<table_name>/edit` | GET, POST | Update a record by primary key |
| `/table/<table_name>/delete` | GET, POST | Delete a record by primary key |
| `/table/add` | GET, POST | Create a new table |
| `/table/delete_table/<table_name>` | POST | Drop a table |
| `/factory_production` | GET | Select a factory production subtype |
| `/factory_production/<subtype_table>` | GET | Joined view of `FACTORY_PRODUCTION` + subtype |
| `/material` | GET | Select a material subtype |
| `/material/<subtype_table>` | GET | Joined view of `MATERIAL` + subtype |

## Getting Started

### Prerequisites

- Python 3.8+
- Microsoft SQL Server (local or remote instance) with a database named `project` containing the schema described above
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Installation

```bash
pip install flask pyodbc
```

### Configuration

Database connection settings live in `get_db_connection()` in `app.py`:

```python
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ER\\SQLEXPRESS01;'
    'DATABASE=project;'
    'Trusted_Connection=yes;'
)
```

Update `SERVER` and `DATABASE` to match your local SQL Server instance name and database. `Trusted_Connection=yes` uses Windows Authentication; switch to SQL Server auth (`UID=...;PWD=...`) if needed.

Login credentials are currently hardcoded in `app.py`:

```python
USER = {'username': 'admin', 'password': 'password123'}
```

### Running the app

```bash
python app.py
```

The app starts in debug mode on `http://127.0.0.1:5000/`.

## Known Limitations / Notes for Future Work

This project was built for a coursework demo against a trusted local database, not for production deployment. Anyone extending it should be aware of:

- **SQL injection risk**: table/column names and some query fragments are interpolated directly into SQL strings (values are parameterized, but identifiers are not and cannot be parameterized in SQL). Since table/column names come from the authenticated UI rather than arbitrary user input, exposure is limited to authenticated users, but this should be hardened (e.g. an identifier allowlist/validator) before any wider deployment.
- **Hardcoded credentials**: a single admin/password pair is defined in source. A real deployment should use hashed passwords in the database and a proper user table.
- **Hardcoded secret key**: `app.secret_key` should be moved to an environment variable.
- **Debug mode**: `app.run(debug=True)` should be disabled in production.
- **No password recovery**: the "Forgot your password?" link on the login page is a placeholder.
- **In-memory table list**: `MANUAL_TABLES` is a Python list mutated at runtime; it resets to its hardcoded values on app restart, so tables created dynamically won't reappear on the dashboard after a restart (though they still exist in the database and can be added back manually).

## Academic Context

Developed as part of a Database Engineering course project, this repository demonstrates:
- EER modeling with supertype/subtype (category) relationships
- Schema normalization
- Translating an ER design into a working relational schema
- Building a data-driven CRUD interface on top of that schema using Python and SQL Server

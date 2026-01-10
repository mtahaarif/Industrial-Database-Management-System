import pyodbc
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USER = {
    'username': 'admin',
    'password': 'password123'
}

MANUAL_TABLES = [
    
    "EMPLOYEE",
    "FACTORY",
    "MAINTENANCE",
    "PARTY",
    "WRAPPED_SECTION"
]

FACTORY_PRODUCTION_SUBTYPES = {
    "ENAMEL_COPPER_WIRE": "Enamel Copper Wire",
    "WRAPPED_SECTION": "Wrapping Section",
    "BARE_STRIP": "Bare Strip",
    "BARE_WIRE": "Bare Wire",
    "SUBMERSIBLE_COPPER_WIRE": "Submersible Copper Wire",
    "COPPER_BRIE": "Copper Tape",
    "ALUMINIUM_ENAMEL_WIRE": "Aluminium Enamel Wire"
}

MATERIAL_SUBTYPES = {
    "RAW_MATERIAL": "Raw Material",
    "FINISHED_MATERIAL": "Finished Material"
}

def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=ER\\SQLEXPRESS01;'
        'DATABASE=project;'
        'Trusted_Connection=yes;'
    )
    return conn


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USER['username'] and request.form['password'] == USER['password']:
            session['user'] = USER['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', tables=MANUAL_TABLES)
    return redirect(url_for('login'))


@app.route('/table/<table_name>', methods=['GET'])
def view_table(table_name):
    if 'user' not in session or table_name not in MANUAL_TABLES:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    attribute = request.args.get('attribute')
    search_query = request.args.get('search_query')

    sql_query = f'SELECT * FROM dbo.[{table_name}]'

    if attribute and search_query:
        sql_query += f' WHERE [{attribute}] LIKE ?'

    cursor.execute(sql_query, ('%' + search_query + '%',) if attribute and search_query else ())
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.close()

    return render_template('table_view.html', table_name=table_name, rows=data, columns=columns)


@app.route('/table/<table_name>/add', methods=['GET', 'POST'])
def add_record(table_name):
    if 'user' not in session or (table_name not in MANUAL_TABLES and table_name not in FACTORY_PRODUCTION_SUBTYPES and table_name not in MATERIAL_SUBTYPES):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        fields = request.form.to_dict()
        query = f'INSERT INTO dbo.[{table_name}] ({", ".join(fields.keys())}) VALUES ({", ".join(["?"] * len(fields))})'
        cursor.execute(query, list(fields.values()))
        conn.commit()
        conn.close()
        flash('Record added successfully.')
        return redirect(url_for('view_table', table_name=table_name))

    cursor.execute(f"SELECT TOP 1 * FROM dbo.[{table_name}]")
    columns = [column[0] for column in cursor.description]
    conn.close()
    return render_template('add_record.html', table_name=table_name, columns=columns)


@app.route('/table/<table_name>/edit', methods=['GET', 'POST'])
def edit_record(table_name):
    if 'user' not in session or (table_name not in MANUAL_TABLES and table_name not in FACTORY_PRODUCTION_SUBTYPES and table_name not in MATERIAL_SUBTYPES):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = ?
    """, table_name)
    attributes = [row[0] for row in cursor.fetchall()]

    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
    AND TABLE_NAME = ?
    """, table_name)
    pk_column = cursor.fetchone()

    if pk_column:
        pk_column_name = pk_column[0]
        cursor.execute(f"SELECT [{pk_column_name}] FROM [{table_name}]")
        record_ids = [row[0] for row in cursor.fetchall()]
    else:
        record_ids = []

    if request.method == 'POST':
        record_id = request.form.get('record_id')
        attribute = request.form.get('attribute')
        new_value = request.form.get('new_value')

        if record_id and attribute and new_value:
            try:
                cursor.execute(f"""
                    UPDATE [{table_name}]
                    SET [{attribute}] = ?
                    WHERE [{pk_column_name}] = ?
                """, (new_value, record_id))
                conn.commit()
                flash('Record updated successfully.')
            except Exception as e:
                flash(f'Error updating record: {str(e)}')
        else:
            flash('Please fill in all fields.')

    conn.close()

    return render_template('edit_record.html',
                           table_name=table_name,
                           record_ids=record_ids,
                           attributes=attributes)


@app.route('/table/<table_name>/delete', methods=['GET', 'POST'])
def delete_record(table_name):
    if 'user' not in session or (table_name not in MANUAL_TABLES and table_name not in FACTORY_PRODUCTION_SUBTYPES and table_name not in MATERIAL_SUBTYPES):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
    AND TABLE_NAME = ?
    """, table_name)
    pk_column = cursor.fetchone()

    if not pk_column:
        flash('No primary key found for this table.')
        return redirect(url_for('dashboard'))

    pk_column_name = pk_column[0]

    cursor.execute(f"SELECT [{pk_column_name}] FROM [{table_name}]")
    record_ids = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        record_id = request.form.get('record_id')
        if record_id:
            try:
                cursor.execute(f"""
                    DELETE FROM [{table_name}]
                    WHERE [{pk_column_name}] = ?
                """, (record_id,))
                conn.commit()
                flash(f'Record {record_id} deleted successfully.')
                return redirect(url_for('delete_record', table_name=table_name))
            except Exception as e:
                flash(f'Error deleting record: {str(e)}')
        else:
            flash('Please select a valid ID to delete.')

    conn.close()

    return render_template('delete_record.html',
                           table_name=table_name,
                           record_ids=record_ids,
                           pk_column=pk_column_name)


@app.route('/table/add', methods=['GET', 'POST'])
def add_table():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        table_name = request.form['table_name'].strip().upper()
        columns = request.form.getlist('columns[]')

        if not table_name or not columns:
            flash('Table name and at least one column is required.')
            return redirect(url_for('add_table'))

        try:
            column_defs = ', '.join([f'[{col.strip()}] NVARCHAR(255)' for col in columns])
            query = f'CREATE TABLE dbo.[{table_name}] (id INT IDENTITY(1,1) PRIMARY KEY, {column_defs})'
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            conn.close()
            MANUAL_TABLES.append(table_name)
            flash(f'Table "{table_name}" created successfully.')
        except Exception as e:
            flash(f'Error creating table: {e}')
        return redirect(url_for('dashboard'))

    return render_template('add_table.html')


@app.route('/table/delete_table/<table_name>', methods=['POST'])
def delete_table(table_name):
    if 'user' not in session or (table_name not in MANUAL_TABLES and table_name not in FACTORY_PRODUCTION_SUBTYPES and table_name not in MATERIAL_SUBTYPES):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE dbo.[{table_name}]')
        conn.commit()
        conn.close()
        MANUAL_TABLES.remove(table_name)
        flash(f'Table "{table_name}" deleted successfully.')
    except Exception as e:
        flash(f'Error deleting table: {e}')

    return redirect(url_for('dashboard'))


@app.route('/factory_production')
def factory_production_selector():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('factory_production.html', subtypes=FACTORY_PRODUCTION_SUBTYPES)


@app.route('/factory_production/<subtype_table>')
def view_factory_production_combined(subtype_table):
    if 'user' not in session or subtype_table not in FACTORY_PRODUCTION_SUBTYPES:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'FACTORY_PRODUCTION' 
            AND CONSTRAINT_NAME LIKE 'PK%'
        """)
        factory_pk = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = '{subtype_table}' 
            AND CONSTRAINT_NAME LIKE 'FK%'
        """)
        subtype_fk = cursor.fetchone()[0]

        query = f"""
        SELECT fp.*, st.*
        FROM dbo.FACTORY_PRODUCTION fp
        INNER JOIN dbo.[{subtype_table}] st ON fp.{factory_pk} = st.{subtype_fk}
        """
        cursor.execute(query)
        joined_rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return render_template(
            'factory_combined_view.html',
            subtype_name=FACTORY_PRODUCTION_SUBTYPES[subtype_table],
            rows=joined_rows,
            columns=columns,
            factory_columns=columns[:len(columns)//2]
        )

    except Exception as e:
        flash(f'Error retrieving data: {str(e)}')
        return redirect(url_for('factory_production_selector'))
    finally:
        conn.close()


@app.route('/material')
def material_selector():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('material_selector.html', subtypes=MATERIAL_SUBTYPES)


@app.route('/material/<subtype_table>')
def view_material_combined(subtype_table):
    if 'user' not in session or subtype_table not in MATERIAL_SUBTYPES:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = 'MATERIAL' 
            AND CONSTRAINT_NAME LIKE 'PK%'
        """)
        material_pk = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = '{subtype_table}' 
            AND CONSTRAINT_NAME LIKE 'FK%'
        """)
        subtype_fk = cursor.fetchone()[0]

        query = f"""
        SELECT m.*, st.*
        FROM dbo.MATERIAL m
        INNER JOIN dbo.[{subtype_table}] st ON m.{material_pk} = st.{subtype_fk}
        """
        cursor.execute(query)
        joined_rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return render_template(
            'material_combined_view.html',
            subtype_name=MATERIAL_SUBTYPES[subtype_table],
            rows=joined_rows,
            columns=columns,
            material_columns=columns[:len(columns)//2]
        )

    except Exception as e:
        flash(f'Error retrieving data: {str(e)}')
        return redirect(url_for('material_selector'))
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)

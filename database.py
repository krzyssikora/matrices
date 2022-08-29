import sqlite3
from matrices.algebra import Matrix
from matrices import config
from matrices.config import _logger
from matrices import matrices_dict, matrices_str_dict, tmp_matrices, matrices_names, assign_answer


def import_from_database():
    """Imports matrices from database to the global dictionary matrices_dict."""
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS matrices
    (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    name STRING, rows INTEGER, columns INTEGER, denominator INTEGER)
    ''')
    cur.execute("SELECT id, name, rows, columns, denominator FROM matrices")
    all_rows = cur.fetchall()
    ids = list()
    for matrix_data in all_rows:
        if matrix_data[1] in matrices_dict:
            continue
        else:
            idx, name, rows, columns, denominator = matrix_data
            cur.execute("SELECT element FROM numerators WHERE matrix_id = ?  ORDER by row, column", (idx,))
            numerators = cur.fetchall()
            values = [(numerator[0], denominator) for numerator in numerators]
            matrices_dict.update({name: Matrix(rows, columns, values)})
    conn.commit()
    cur.close()
    return matrices_dict


def delete_matrix(m_name, fully=True):
    """Deletes the matrix from the database and, optionally, from the global matrices_dict dictionary.

    Args:
        m_name (str): A name, as in matrices_dict, not an actual object.
        fully (bool) - whether to delete from the matrices_dict, too
        fully = False is used in case of overwriting, i.e. creating a new matrix and storing it on an existing one.
        In such a case the matrix previously labeled with this name should be removed from the database,
        but in the dictionary an update is sufficient.
    """
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS matrices
    (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    name STRING, rows INTEGER, columns INTEGER, denominator INTEGER)
    ''')
    cur.execute('''CREATE TABLE IF NOT EXISTS numerators
    (matrix_id INTEGER, row INTEGER, column INTEGER, element INTEGER)''')
    cur.execute('SELECT id FROM matrices WHERE name = ?', (m_name,))
    row = cur.fetchone()
    m_id = row[0]
    cur.execute('DELETE FROM matrices WHERE id = ?', (m_id,))
    cur.execute('DELETE FROM numerators WHERE matrix_id = ?', (m_id,))
    conn.commit()
    cur.close()
    if fully:
        del matrices_dict[m_name]
        print(f"The matrix {m_name} has been deleted from the database.")


def save_matrix(m_name):
    """Saves the matrix in the database.

        Args:
            m_name (str): A name, as in matrices_dict, not an actual object.

        Returns None if the matrix was not added to the global matrices_dic dictionary.
    """
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS matrices
    (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    name STRING, rows INTEGER, columns INTEGER, denominator INTEGER)
    ''')
    cur.execute('''CREATE TABLE IF NOT EXISTS numerators
    (matrix_id INTEGER, row INTEGER, column INTEGER, element INTEGER)''')

    matrix = matrices_dict.get(m_name, None)
    if matrix is None:
        return None
    cur.execute('SELECT id FROM matrices WHERE name = ?', (m_name,))
    row = cur.fetchone()
    if row is None:
        cur.execute('''INSERT INTO matrices
        (name, rows, columns, denominator)
        VALUES (?, ?, ?, ?)''', (m_name, matrix.rows, matrix.columns, matrix.denominator))
        cur.execute('SELECT id FROM matrices WHERE name = ?', (m_name,))
        m_id = cur.fetchone()[0]
        for row in range(matrix.rows):
            for column in range(matrix.columns):
                cur.execute('INSERT INTO numerators (matrix_id, row, column, element) VALUES (?, ?, ?, ?)',
                            (m_id, row, column, matrix.mat[row][column]))
    conn.commit()
    cur.close()

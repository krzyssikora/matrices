import sqlite3
from matrices.algebra import Matrix
from matrices import config
# from matrices.config import _logger


def import_from_database():
    """Imports matrices from database to the global dictionary matrices_dict."""
    matrices_dict = dict()
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT id, name, rows, columns, denominator FROM matrices")
    all_rows = cur.fetchall()
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


def delete_matrix(m_name):
    """Deletes the matrix from the database and, optionally, from the global matrices_dict dictionary.

    Args:
        m_name (str): A name, as in matrices_dict, not an actual object.
    """
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT id FROM matrices WHERE name = ?', (m_name,))
    row = cur.fetchone()
    m_id = row[0]
    cur.execute('DELETE FROM matrices WHERE id = ?', (m_id,))
    cur.execute('DELETE FROM numerators WHERE matrix_id = ?', (m_id,))
    conn.commit()
    cur.close()


def save_matrix(m_name, matrices_dict):
    """Saves the matrix in the database.

        Args:
            m_name (str): A name, as in matrices_dict, not an actual object.
            matrices_dict (dict):

        # Returns None if the matrix was not added to the global matrices_dic dictionary.
    """
    matrix = matrices_dict.get(m_name, None)
    if matrix is None:
        return
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
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

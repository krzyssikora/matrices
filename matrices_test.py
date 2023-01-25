import pytest
from matrices import utils
from matrices import algebra

MATRICES_DICT = {
    'A': algebra.Matrix(2, 2, [(1, 1), (2, 1), (3, 1), (4, 1)]),
    'B': algebra.Matrix(2, 3, [(-1, 1), (1, 2), (0, 1), (3, 1), (-2, 1), (1, 3)]),
    'Ainv': algebra.Matrix(2, 2, [(-2, 1), (1, 1), (3, 2), (-1, 2)]),
    'AB': algebra.Matrix(2, 3, [(5, 1), (-7, 2), (2, 3), (9, 1), (-13, 2), (4, 3)]),
    'ZERO2': algebra.Matrix(2, 2, [(0, 1), (0, 1), (0, 1), (0, 1)]),
    'A3': algebra.Matrix(2, 6, [(1, 1), (2, 1), (1, 1), (2, 1), (1, 1), (2, 1),
                                (3, 1), (4, 1), (3, 1), (4, 1), (3, 1), (4, 1)]),

}
IN_OUTS = [
    ('2*2', (4, 1)),
    ('A', MATRICES_DICT['A']),
    ('1/0', None),
    ('A^(-1)', MATRICES_DICT['Ainv']),
    ('A^-1', MATRICES_DICT['Ainv']),
    ('A*B', MATRICES_DICT['AB']),
    ('B*A', None),
    ('2*A-A-A', MATRICES_DICT['ZERO2']),
    ('A^2-A*A', MATRICES_DICT['ZERO2']),
    ('AUG(AUG(A,A),A)', MATRICES_DICT['A3']),
    ('AUG(A,AUG(A,A))', MATRICES_DICT['A3']),
    ('(4-2)^3', (8, 1)),
    ('2^(5-2)', (8, 1)),
    ('(4-2)^(5-2)', (8, 1)),
    ('2^(3^2)', (512, 1)),
    ('2^3^2', (512, 1)),
    ('(2^3)^2', (64, 1)),
    ('2^(3-2)+(4-2)^3-(3-1)^(5-3)', (6, 1)),
    ('2^(3-2)+(4-2)^3-(3-1)^(5-3) + 2^3^2', (518, 1)),
]


def simplify_output(output_value):
    rows, columns, string_values = output_value['rows'], output_value['columns'], output_value['values']
    values = list()
    for value in string_values:
        value = value.replace('minussign', '-')
        slash_pos = value.find('slashsign')
        mat_value = (int(value[:slash_pos]), int(value[slash_pos + 9:]))
        values.append(mat_value)
    return algebra.Matrix(rows, columns, values)


def test_results():
    for user_input, output in IN_OUTS:
        input_processed, input_latexed, refresh_storage, saveable, output_value = \
            utils.get_input_read(user_input, MATRICES_DICT)
        if isinstance(output_value, dict):
            output_value = simplify_output(output_value)
        assert output_value == output


if __name__ == '__main__':
    test_results()

# h=a
# del(a,b)
# del(a)
# del a

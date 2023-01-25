# import pytest
import utils
import algebra

MATRICES_DICT = {
    'A': algebra.Matrix(2, 2, [(1, 1), (2, 1), (3, 1), (4, 1)])

}
IN_OUTS = [
    ('2*2', (4, 1)),
    ('A', MATRICES_DICT['A']),
    ('1/0', 0)
]


def test_results():
    for user_input, output in IN_OUTS:
        input_processed, input_latexed, refresh_storage, saveable, output_value = \
            utils.get_input_read(user_input, MATRICES_DICT)
        print(user_input)
        print(input_processed, input_latexed, refresh_storage, saveable, output_value)
        print()
        # assert output_value == output


# a
# b*a, a*b (one not possible)
# 2*a-a-a
# a^2-a*a
# aug(aug(a,a),a)
# aug(a,aug(a,a))
# h=a
# del(a,b)
# del(a)
# del a
# (4-2)^3
# 2^(5-2)
# (4-2)^(5-2)
# 2^(3^2)
# 2^3^2
# 2^(3-2)+(4-2)^3-(3-1)^(5-3)
# 2^(3-2)+(4-2)^3-(3-1)^(5-3) + 2^3^2
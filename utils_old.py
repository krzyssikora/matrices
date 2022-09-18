# from matrices.algebra import Matrix
from matrices import database, algebra, config
from matrices.config import _logger
import re
import math


def mathjax_wrap(ltx_string):
    return r'\( {} \)'.format(ltx_string)


def get_list_of_matrix_dict_latexed(m_dict):
    m_list = list()
    for name, matrix in m_dict.items():
        m_list.append((name, mathjax_wrap('{}={}'.format(name, matrix.get_latex_form()))))
    m_list.sort()
    return m_list


def find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples, search_value, which_coordinate=0, idx_from=None, idx_to=None):
    """
    binary search of a tuple with known certain coordinate
    Args:
        list_of_tuples:
        search_value:
        which_coordinate:
        idx_from:
        idx_to:
    Returns:
        The tuple with which_coordinate equal to search_value or None if there is no such tuple.
    """
    list_of_tuples.sort()
    if idx_from is None:
        idx_from = 0
    if idx_to is None:
        idx_to = len(list_of_tuples) - 1

    if idx_from == idx_to or idx_to - idx_from == 1:
        if list_of_tuples[idx_from][which_coordinate] == search_value:
            return list_of_tuples[idx_from]
        elif list_of_tuples[idx_to][which_coordinate] == search_value:
            return list_of_tuples[idx_to]
        else:
            return None

    idx_mid = (idx_from + idx_to) // 2
    pivot = list_of_tuples[idx_mid][which_coordinate]
    if pivot == search_value:
        return list_of_tuples[idx_mid]
    elif pivot < search_value:
        return find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples, search_value, which_coordinate, idx_mid, idx_to)
    elif pivot > search_value:
        return find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples, search_value, which_coordinate, idx_from, idx_mid)


def get_inner_pair_id(brackets, idx):
    start_pos, end_pos = brackets[idx]
    while True:
        idx += 1
        if idx >= len(brackets):
            return None
        if brackets[idx][1] < end_pos:
            return idx


def get_signs_tidied_up(input_string):
    pos_0 = 0
    while True:
        if pos_0 >= len(input_string):
            break
        if input_string[pos_0] in {'+', '-'}:
            pos_1 = pos_0 + 1
            while True:
                if pos_1 >= len(input_string) or input_string[pos_1] not in {'+', '-'}:
                    break
                pos_1 += 1
            if pos_1 > pos_0 + 1:
                pluses_and_minuses = input_string[pos_0: pos_1]
                sgn = '-' if eval(pluses_and_minuses + '1') < 0 else '+'
                input_string = input_string[:pos_0] + sgn + input_string[pos_1:]
        pos_0 += 1
    return input_string


def get_front_minuses_and_pluses(the_string):
    pos = 0
    minuses_and_pluses = ''
    while True:
        if pos == len(the_string):
            break
        if the_string[pos] in {'+', '-'}:
            minuses_and_pluses += the_string[pos]
            pos += 1
        else:
            break
    return minuses_and_pluses


def get_number_from_string(fraction_as_string):
    """Changes a string that represents a fraction into a tuple (numerator, denominator).
    Args:
        fraction_as_string (str): can be in a form of a decimal (e.g. "1.25"), a fraction ("34/56") or an integer.

    Returns:
        A tuple (numerator, denominator).
    """
    while fraction_as_string[0] == '(' and fraction_as_string[-1] == ')':
        fraction_as_string = fraction_as_string[1:-1]
    fraction_as_string = str(fraction_as_string)
    minuses_and_pluses = get_front_minuses_and_pluses(fraction_as_string)
    fraction_as_string = fraction_as_string[len(minuses_and_pluses):]
    sgn = eval(minuses_and_pluses + '1')
    if fraction_as_string == '':  # a field left blank is to result in 0
        return 0, 1
    elif '/' in fraction_as_string:
        slash_position = fraction_as_string.find("/")
        numerator = int(fraction_as_string[:slash_position])
        den = int(fraction_as_string[slash_position + 1:])
        if den < 0:
            numerator, den = -numerator, -den
    elif '.' in fraction_as_string:
        n = 0
        numerator = float(fraction_as_string)
        while True:
            if numerator == int(numerator):
                break
            else:
                numerator *= 10
                n += 1
        numerator = int(numerator)
        den = int(10 ** n)
    elif float(fraction_as_string) == int(float(fraction_as_string)):
        return int(float(fraction_as_string)), 1
    else:
        return None, None
    div = math.gcd(den, numerator)
    numerator = int(numerator / div)
    den = int(den / div)
    return sgn * numerator, den


def is_fraction(the_string):
    while len(the_string) > 0 and the_string[0] in {'-', '+'}:
        the_string = the_string[1:]
    if the_string.count('/') != 1:
        return False
    pos = the_string.find('/')
    if pos == 0 or pos == len(the_string) - 1:
        return False
    if the_string[:pos].isdigit() and the_string[pos + 1:].isdigit():
        return True
    return False


def is_decimal(the_string):
    while len(the_string) > 0 and the_string[0] in {'-', '+'}:
        the_string = the_string[1:]
    if the_string.count('.') != 1:
        return False
    pos = the_string.find('.')
    if pos == len(the_string) - 1:
        return False
    if (len(the_string[:pos]) == 0 or the_string[:pos].isdigit()) and the_string[pos + 1:].isdigit():
        return True
    return False


def is_integer(the_string):
    while len(the_string) > 0 and the_string[0] in {'-', '+'}:
        the_string = the_string[1:]
    return the_string.isdigit()


def is_matrix(the_string, matrices_dict, tmp_matrices):
    while len(the_string) > 0 and the_string[0] in {'-', '+'}:
        the_string = the_string[1:]
    if the_string in matrices_dict or the_string in tmp_matrices:
        return True


def find_position_of_an_integer_in_string(input_string, starting_id, go_left, tmp_fractions,
                                          string_in_progress, latex_in_progress):
    # if o denotes a char with starting_id, we want to find
    # .....(...)o(...)......    or
    # .....11111o22222......
    #      ^   ^ ^   ^          if go_left is True / False
    #      T   T F   F
    """
    returns the other id (starting - ending)
    Updates tmp_fractions and changes ..._in_progress
    Args:
        input_string:
        starting_id:
        go_left:
        tmp_fractions:

    Returns:

    """
    def stop_condition(str_len, temp_id, go_l):
        ret_bool = (temp_id < 0) if go_l else (temp_id >= str_len)
        return ret_bool

    shift = -1 if go_left else 1
    idx = starting_id
    min_len = 1
    if not go_left and input_string[idx + 1] in {'+', '-'}:
        idx += 1
        min_len = 2
    while True:
        idx += shift
        if stop_condition(len(input_string), idx, go_left):
            break
        if not input_string[idx].isdigit():
            break
    if go_left and input_string[idx] in {'+', '-'}:
        idx -= 1
        min_len = 2
    idx += 1 * go_left
    starting_id += 1 * (not go_left)
    if (idx - starting_id) * (-1 if go_left else 1) < min_len:
        return None

    # change the number into an element of tmp_fractions
    if go_left:
        pos_0, pos_1 = idx, starting_id
    else:
        pos_0, pos_1 = starting_id, idx
    the_number = get_number_from_string(input_string[pos_0, pos_1])
    new_fraction_idx = len(tmp_fractions)
    new_fraction_name = f'F_{new_fraction_idx}'
    tmp_fractions[new_fraction_name] = the_number
    string_in_progress[pos_0] = new_fraction_name
    latex_in_progress[pos_0] = input_string[pos_0, pos_1]
    for k in range(pos_0 + 1, pos_1):
        string_in_progress[k] = None
        latex_in_progress[k] = ''

    return idx


def find_position_of_a_fraction_in_string(input_string, string_in_process, latex_in_process, read_range,
                                          matrices_dict, tmp_matrices, tmp_fractions,
                                          brackets_all, brackets_opening, brackets_closing,
                                          starting_id, go_left, input_iteration=0):
    # if o denotes a char with starting_id, we want to find
    # .....(...)o(...)......    or
    # .....11111o22222......
    #      ^   ^ ^   ^          if go_left is True / False
    #      T   T F   F
    def stop_condition(str_len, temp_id, go_l):
        ret_bool = (temp_id < 0) if go_l else (temp_id >= str_len)
        return ret_bool

    if brackets_all is None:
        brackets_all, brackets_opening, brackets_closing = get_pairs_of_brackets_from_string(input_string)[0]
    if brackets_all:
        if go_left:
            the_tuple = find_tuple_in_list_of_tuples_by_coordinate(brackets_all, starting_id - 1, 1)
        else:
            the_tuple = find_tuple_in_list_of_tuples_by_coordinate(brackets_all, starting_id + 1, 0)
        if the_tuple:
            is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
                read_input(input_string, string_in_process, latex_in_process, read_range,
                           matrices_dict, tmp_matrices, tmp_fractions,
                           brackets_all, brackets_opening, brackets_closing,
                           input_iteration + 1)
            if string_in_process[the_tuple[0]] in tmp_fractions:
                return the_tuple[0]
            else:
                return None


def find_position_of_a_matrix_in_string(input_string, string_in_process, latex_in_process, read_range,
                                        matrices_dict, tmp_matrices, tmp_fractions,
                                        brackets_all, brackets_opening, brackets_closing,
                                        starting_id, go_left, input_iteration=0):
    """

    Args:
        input_string:
        string_in_process:
        latex_in_process:
        read_range:
        matrices_dict:
        tmp_matrices:
        tmp_fractions:
        brackets_all:
        brackets_opening:
        brackets_closing:
        starting_id:
        go_left:
        input_iteration:
        brackets:

    Returns:
        the other position of a matrix (left if go_left is True, right otherwise)
        or None if matrix does not start there
    """
    # if o denotes a char with starting_id, we want to find
    # .....(...)o(...)......    or
    # .....M_111oM_222......
    #      ^   ^ ^   ^          if go_left is True / False
    #      T   T F   F
    if brackets_all is None:
        brackets_all, brackets_opening, brackets_closing = get_pairs_of_brackets_from_string(input_string)[0]
    if brackets_all:
        if go_left:
            the_tuple = find_tuple_in_list_of_tuples_by_coordinate(brackets_all, starting_id - 1, 1)
        else:
            the_tuple = find_tuple_in_list_of_tuples_by_coordinate(brackets_all, starting_id + 1, 0)
        if the_tuple:
            is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
                read_input(input_string, string_in_process, latex_in_process, read_range,
                           matrices_dict, tmp_matrices, tmp_fractions,
                           brackets_all, brackets_opening, brackets_closing,
                           input_iteration + 1)
            if string_in_process[the_tuple[0]] in matrices_dict or string_in_process[the_tuple[0]] in tmp_matrices:
                return the_tuple[0]
            else:
                return None

    shift = -1 if go_left else 1
    idx = starting_id
    if go_left:
        for matrix_name in list(matrices_dict) + list(tmp_matrices):
            pos = input_string[:starting_id + 1].rfind(matrix_name)
            if pos >= 0 and pos + len(matrix_name) == starting_id + 1:
                return pos
    else:
        for matrix_name in list(matrices_dict) + list(tmp_matrices):
            pos = input_string.find(matrix_name, starting_id)
            if pos == starting_id:
                return pos + len(matrix_name) - 1
    return None


def insert_latex_indices(input_string):
    # firstly deal with 'M^T' and 'M^(T)' -> 'M^{T}'
    for idx in {'^(T)', '^T'}:
        while True:
            pos = input_string.find(idx)
            if pos < 0:
                break
            input_string = input_string[:pos + 1] + '{T}' + input_string[pos + len(idx):]

    # now deal with 'M^(...)' -> 'M^{...}'
    brackets = algebra.get_pairs_of_brackets_from_string(input_string)
    starts_of_indices = [idx + 1 for idx in range(len(input_string)) if input_string[idx] == '^'
                         if (idx + 1 < len(input_string) and input_string[idx + 1] != '{')]
    remaining_pos = list()
    for start_pos in starts_of_indices:
        if input_string[start_pos] == '(':
            both_pos = find_tuple_in_list_of_tuples_by_coordinate(brackets, start_pos)
            if both_pos:
                end_pos = both_pos[1]
                input_string = \
                    input_string[:start_pos] + '{' + \
                    input_string[start_pos + 1: end_pos] + '}' + input_string[end_pos + 1:]
        else:
            remaining_pos.append(start_pos)

    # now deal with 'M^-10' -> 'M^{-10}' and with 'M^10' -> 'M^{10}'
    indices_to_tackle = list()
    for start_pos in remaining_pos:
        end_pos = start_pos
        if ord(input_string[end_pos]) == ord("-"):
            end_pos += 1
        while end_pos < len(input_string) and input_string[end_pos].isdigit():
            end_pos += 1
        if end_pos < start_pos:
            continue
        indices_to_tackle.append((start_pos, end_pos))

    indices_to_tackle.sort()
    # find inner indicies: ...^(...^(...)...)
    # 1. find an inner index
    # 2. add curly braces to the string
    # 3. remove the tuple with the index from the list
    # 4. add 2 to all following indicies
    # 5. break when no inner left
    idx = 0
    while True:
        if idx >= len(indices_to_tackle):
            break
        inner_id = get_inner_pair_id(indices_to_tackle, idx)
        if inner_id:
            start_pos, end_pos = indices_to_tackle[inner_id]
            input_string = \
                input_string[:start_pos] + '{' + input_string[start_pos + 1: end_pos] + '}' + input_string[end_pos + 1:]
            indices_to_tackle.pop(inner_id)
            for i in range(inner_id, len(indices_to_tackle)):
                indices_to_tackle[i] = (indices_to_tackle[i][0] + 2, indices_to_tackle[i][1] + 2)
        else:
            idx += 1

    # all inner removed, so only mutually exclusive left
    indices_to_tackle.sort(reverse=True)
    for start_pos, end_pos in indices_to_tackle:
        input_string = input_string[:start_pos] + '{' + input_string[start_pos: end_pos] + '}' + \
                       input_string[end_pos:]

    return input_string


def insert_latex_fractions(input_string):
    # todo: missing arguments of find_position_of_a_number...
    while True:
        idx = input_string.find('/')
        if idx == -1:
            break
        id_before_start, id_before_end = find_position_of_an_integer_in_string(input_string, idx, True, None), idx - 1
        id_after_start, id_after_end = idx + 1, find_position_of_an_integer_in_string(input_string, idx, False, None)
        input_string = \
            input_string[:id_before_start] + '\\frac{' + \
            input_string[id_before_start: id_before_end] + '}{' + \
            input_string[id_after_start: id_after_end] + '}' + input_string[id_after_end:]
    return input_string


def insert_latex_multiplications(input_string):
    multiplication_signs_ids = [idx for idx in range(len(input_string)) if input_string[idx] == '*']
    multiplication_signs_ids.sort(reverse=True)
    for idx in multiplication_signs_ids:
        input_string = input_string[:idx] + '\\times ' + input_string[idx + 1:]
    return input_string


def change_latex_restricted_words(input_string):
    for restricted_word in {'rref', 'del', 'aug', 'sub', 'det'}:
        word = restricted_word.upper()
        pos = -6 - len(word)
        while True:
            pos = input_string.find(word, pos + len(word) + 6)
            if pos < 0:
                break
            input_string = input_string[:pos] + '\\text{{{}}}'.format(word.lower()) + input_string[pos + len(word):]

    for restricted_word_with_prefix in {('ref', 'r')}:
        restricted_word, prefix = restricted_word_with_prefix
        word = restricted_word.upper()
        pos = -6 - len(word) - len(prefix)
        while True:
            pos = input_string.find(word, pos + len(prefix) + len(word) + 6)
            if pos < 0:
                break
            if input_string[pos - 1: pos + len(word) + len(prefix) - 1].lower() == (prefix + word).lower():
                break
            input_string = input_string[:pos] + '\\text{{{}}}'.format(word.lower()) + input_string[
                                                                                       pos + len(word):]
    return input_string


def change_to_latex(input_string):
    # _logger.debug('input before processing    : {}'.format(input_string))
    input_string = insert_latex_indices(input_string)
    # _logger.debug('input after indices        : {}'.format(input_string))
    input_string = insert_latex_fractions(input_string)
    # _logger.debug('input after fractions      : {}'.format(input_string))
    input_string = insert_latex_multiplications(input_string)
    # _logger.debug('input after multiplications: {}'.format(input_string))
    input_string = change_latex_restricted_words(input_string)
    # _logger.debug('input after restr. words: {}'.format(input_string))
    return input_string


def remove_redundant_brackets(input_string, brackets):
    """Removes unnecessary brackets and does bracketing again.

    Then it does bracketing again (i.e. parses pairs of opening and closing brackets and creates respective lists)

    Args:
        input_string (str): A string to be searched through and simplified.
        brackets (list): list of tuples (opening, closing) of indexes of brackets in input_string

    Returns the simplified input_string and three lists with brackets' indexes.
    """
    new_brackets = list()
    for elt in brackets:
        if [elt[0] - 1, elt[1] + 1] in brackets:
            continue
        else:
            new_brackets.append([elt[0], elt[1]])
    if [0, len(input_string) - 1] in new_brackets:
        new_brackets.remove([0, len(input_string) - 1])
    for elt in brackets:
        if elt in new_brackets:
            continue
        else:
            input_string = input_string[:elt[0]] + " " \
                           + input_string[elt[0] + 1: elt[1]] + " " + input_string[elt[1] + 1:]
    # removes unnecessary brackets around T
    while "(T)" in input_string:
        input_string = input_string.replace("(T)", "T")
    # remove spaces
    input_string = input_string.replace(" ", "")
    brackets, brackets_open, brackets_close = get_pairs_of_brackets_from_string(input_string)
    if brackets is None:
        return None
    return input_string, brackets, brackets_open, brackets_close


def get_pairs_of_brackets_from_string(input_string, opening_char="(", closing_char=")"):
    """Creates a list of pairs of positions of opening and closing brackets.

    Args:
        input_string (str): A string to be parsed.
        opening_char (str): A character used for opening bracket.
        closing_char (str): A character used for closing bracket.

    Returns:
        three lists:
        1. a list of tuples: (opening_index, closing_index) of pairs of indexes of opening and closed brackets
        2. a list of opening indexes
        3. a list of closing indexes
    """
    return_pairs_of_brackets = list()
    openings = [i for i in range(len(input_string)) if input_string[i] == opening_char]
    closings = [i for i in range(len(input_string)) if input_string[i] == closing_char]
    if len(openings) != len(closings):
        return None
    ind = 0
    # pairs the brackets, i.e. finds an opening bracket such that the next bracket is a closing one,
    # appends the pair to the final list and removes both brackets from openings / closings
    while True:
        if len(openings) == 0:
            break
        opening = openings[ind]
        closing = input_string.find(closing_char, opening)
        while closing not in closings:
            closing = input_string.find(closing_char, closing + 1)
        if closing < opening:
            return None
        if ind + 1 == len(openings) or openings[ind + 1] > closing:
            # either last opening or next is further than closing
            if closing - opening == 1:  # do not allow empty brackets
                return None
            return_pairs_of_brackets.append((opening, closing))
            openings.remove(opening)
            closings.remove(closing)
            ind = max(0, ind - 1)
        else:
            ind += 1
        print(ind)
    if len(closings) > 0:
        return None
    return_pairs_of_brackets.sort()

    return return_pairs_of_brackets, [b[0] for b in return_pairs_of_brackets], [b[1] for b in return_pairs_of_brackets]


def other_brackets_collide_with_brackets(brackets, other_brackets):
    # check whether any of other_brackets does not collide with brackets
    for opening, closing in brackets:
        for other_opening, other_closing in other_brackets:
            if opening < other_opening < closing < other_closing or other_opening < opening < other_closing < closing:
                return True
    return False


def get_brackets_simplified(input_string):
    """
    Checks whether brackets of different types are correctly placed and if so, changes all of them to round brackets.
    Args:
        input_string
    Returns:
        input_string with brackets replaced or None if they are incorrectly places
    """
    brackets_round = get_pairs_of_brackets_from_string(input_string)
    if brackets_round is None:
        return None
    brackets_square = get_pairs_of_brackets_from_string(input_string, '[', ']')
    if brackets_square is None:
        return None
    brackets_curly = get_pairs_of_brackets_from_string(input_string, '{', '}')
    if brackets_curly is None:
        return None

    all_brackets = {brackets_round, brackets_square, brackets_curly}
    for brackets in all_brackets:
        all_other_brackets = all_brackets.difference({brackets})
        for other_brackets in all_other_brackets:
            if other_brackets_collide_with_brackets(brackets[0], other_brackets[0]):
                return None

    for old, new in {('{', '('), ('}', ')'), ('[', '('), (']', ')')}:
        input_string = input_string.replace(old, new)

    brackets = get_pairs_of_brackets_from_string(input_string)
    input_string, brackets, brackets_open, brackets_close = remove_redundant_brackets(input_string, brackets[0])

    return input_string


def get_mutually_exclusive_brackets(brackets):
    mutually_exclusive_brackets = list()
    idx = 0
    pivot = -1
    while True:
        if brackets[idx][0] > pivot:
            mutually_exclusive_brackets.append(brackets[idx])
            pivot = brackets[idx][1]
        idx += 1
        if idx >= len(brackets):
            break
    mutually_exclusive_brackets.sort(reverse=True)
    return mutually_exclusive_brackets


def read_input_within_brackets(input_string, string_in_process, latex_in_process,
                               matrices_dict, tmp_matrices, tmp_fractions,
                               brackets_all, brackets_opening, brackets_closing,
                               input_iteration):
    mutually_exclusive_brackets = get_mutually_exclusive_brackets(brackets_all)
    is_outcome_valid = None
    for opening_index, closing_index in mutually_exclusive_brackets:
        is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
            read_input(input_string, string_in_process, latex_in_process,
                       (opening_index + 1, closing_index),
                       matrices_dict, tmp_matrices, tmp_fractions,
                       brackets_all, brackets_opening, brackets_closing,
                       input_iteration + 1)
        if not is_outcome_valid:
            break

    return is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions


def get_multiple_input_processed(input_string, string_in_process, latex_in_process, read_range,
                                 matrices_dict, tmp_matrices, tmp_fractions,
                                 brackets_all, brackets_opening, brackets_closing,
                                 iteration,
                                 number_of_parameters):
    """Inserts a list of terms separated by commas into string_in_progress.

    A term makes sense if it is a matrix or a tuple or a string.

    Args:
        input_string (str): A string to be searched through and simplified.
        string_in_process:
        latex_in_process:
        read_range:
        matrices_dict:
        tmp_matrices:
        tmp_fractions:
        brackets_all:
        brackets_opening:
        brackets_closing:
        iteration:
        number_of_parameters (int): The required number of terms to be found.

    Returns:
        is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions
    """
    starting_position, ending_position = read_range
    if number_of_parameters == 1:
        return read_input(input_string, string_in_process, latex_in_process, read_range,
                          matrices_dict, tmp_matrices, tmp_fractions,
                          brackets_all, brackets_opening, brackets_closing,
                          iteration + 1)

    num_commas = input_string[starting_position: ending_position].count(',')
    if num_commas + 1 < number_of_parameters:
        return None
    pos = starting_position - 1
    while True:
        pos = input_string[:ending_position].find(",", pos + 1)
        if pos == -1:
            return None
        # head is the part before the chosen comma
        is_head_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
            read_input(input_string, string_in_process, latex_in_process, (0, pos),
                       matrices_dict, tmp_matrices, tmp_fractions,
                       brackets_all, brackets_opening, brackets_closing,
                       iteration + 1)
        # tail is the rest, split recursively
        is_tail_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
            get_multiple_input_processed(input_string, string_in_process, latex_in_process,
                                         (pos + 1, len(input_string)),
                                         matrices_dict, tmp_matrices, tmp_fractions,
                                         brackets_all, brackets_opening, brackets_closing,
                                         iteration + 1, number_of_parameters - 1)
        if not (is_head_valid and is_tail_valid):
            continue
        else:
            tail = string_in_process[pos + 1]
            string_in_process[0] = [string_in_process[0]] + tail if isinstance(tail, list) else [tail]
            # todo do we need the part below, above return? Or is it cleared deeper in read_input?
            for k in range(1, len(string_in_process)):
                string_in_process[k] = None
            for k in range(len(string_in_process)):
                latex_in_process[k] = ''
            return True, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions
    return False, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions


def prefix_functions(prefix,
                     input_string, string_in_process, latex_in_process, read_range,
                     matrices_dict, tmp_matrices, tmp_fractions,
                     brackets_all, brackets_opening, brackets_closing,
                     input_iteration):
    """
    Args:
        prefix:
        input_string:
        string_in_process:
        latex_in_process:
        read_range:
        matrices_dict:
        tmp_matrices:
        tmp_fractions:
        brackets_all:
        brackets_opening:
        brackets_closing:
        input_iteration:

    Returns:
        is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions
    """
    # deals with functions in the input_string of the form: func(...)
    # where prefix = "func("
    # inserts an appropriate result (tmp matrix's name or a tmp fraction's name) into string_in_progress
    starting_position, ending_position = read_range
    m_result = m_name = None
    incorrect_input_return_values = (False, f'Incorrect input of "{prefix[:-1]}"', 'input not processed',
                                     matrices_dict, tmp_matrices, tmp_fractions)
    while True:
        pos0 = input_string[:ending_position].find(prefix, starting_position)
        if pos0 == -1:
            break
        pos1 = pos0 + len(prefix) - 1
        if pos1 < ending_position and pos1 in brackets_opening:
            # pos0 points to the first letter of prefix,
            # pos1 and pos2 point to the opening and closing brackets
            pos2 = brackets_all[brackets_opening.index(pos1)][1]
            # firstly functions that can have multiple inputs
            if prefix in ["AUG(", "SUB(", "CREATE("]:
                which_prefix = ["AUG(", "SUB(", "CREATE("].index(prefix)
                number_of_parameters = which_prefix + [2, 2, 0][which_prefix]

                is_outcome_valid, pref_string_in_process, pref_latex_in_process, \
                    matrices_dict, tmp_matrices, tmp_fractions \
                    = get_multiple_input_processed(input_string, string_in_process, latex_in_process,
                                                   (pos1 + 1, pos2),
                                                   matrices_dict, tmp_matrices, tmp_fractions,
                                                   brackets_all, brackets_opening, brackets_closing,
                                                   input_iteration,
                                                   number_of_parameters)
                if not is_outcome_valid and prefix == "SUB(":
                    number_of_parameters += 2
                    is_outcome_valid, pref_string_in_process, pref_latex_in_process, \
                        matrices_dict, tmp_matrices, tmp_fractions \
                        = get_multiple_input_processed(input_string, string_in_process, latex_in_process,
                                                       (pos1 + 1, pos2),
                                                       matrices_dict, tmp_matrices, tmp_fractions,
                                                       brackets_all, brackets_opening, brackets_closing,
                                                       input_iteration,
                                                       number_of_parameters)
                multiple_input = string_in_process[pos1 + 1]
                if not is_outcome_valid:
                    return incorrect_input_return_values
                elif prefix == "AUG(" \
                        and isinstance(multiple_input, list) \
                        and isinstance(multiple_input[0], algebra.Matrix) \
                        and isinstance(multiple_input[1], algebra.Matrix):
                    m_result = multiple_input[0].augment(multiple_input[1])
                elif prefix == "SUB(":  # not resistant to mistakes
                    sub_inp = list()
                    for i in range(number_of_parameters - 1):
                        if isinstance(multiple_input[1:][i], tuple):
                            sub_inp.append(multiple_input[1:][i][0])
                        else:
                            return incorrect_input_return_values
                    if isinstance(multiple_input[0], algebra.Matrix):
                        m_result = multiple_input[0].submatrix(*sub_inp)
                    else:
                        return incorrect_input_return_values
                # elif prefix == "CREATE(":
                #     if isinstance(multiple_input[0], tuple) and multiple_input[0][1] == 1:
                #         rows = multiple_input[0][0]
                #         try:
                #             rows = int(rows)
                #         except Exception as e:
                #             print(e)
                #             return None
                #     else:
                #         return None
                #     if isinstance(multiple_input[1], tuple) and multiple_input[1][1] == 1:
                #         columns = multiple_input[1][0]
                #         try:
                #             columns = int(columns)
                #         except Exception as e:
                #             print(e)
                #             return None
                #     else:
                #         return None
                #     m_result = algebra.Matrix(rows, columns)
                    # todo: it was: m_result = Matrix(rows, columns, random_assignment=True)
                    # if assign_answer[0]:
                    #     assign_answer[0] = False
                    #     print("Matrix " + assign_answer[2] + ":")
                    #     print(m_result)
                    #     matrices_dict.update({assign_answer[2]: m_result})
                    #     database.save_matrix(assign_answer[2])
                    #     assign_answer[2] = ""
                    #     if assign_answer[1]:
                    #         assign_answer[1] = False
                    #         print("has been changed.")
                    #     else:
                    #         print("has been created.")
                    #     return ""
            # then functions without an input
            else:
                is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
                    read_input(input_string, string_in_process, latex_in_process, (pos1 + 1, pos2),
                               matrices_dict, tmp_matrices, tmp_fractions,
                               brackets_all, brackets_opening, brackets_closing,
                               input_iteration + 1)
                function_input = string_in_process[pos1 + 1]
                if not is_outcome_valid or isinstance(function_input, tuple):
                    return incorrect_input_return_values
                elif isinstance(function_input, algebra.Matrix):  # argument of the function is a matrix
                    list_prefixes = ["RREF(", "REF(", "DET("]
                    list_functions = [function_input.rref(), function_input.ref(), function_input.det()]
                    m_result = list_functions[list_prefixes.index(prefix)]
            # places a tmp matrix or tmp fraction name in string_in_process
            # create temporary matrix / fraction
            m_index = len(tmp_matrices)
            if m_result is None:
                return incorrect_input_return_values
            elif isinstance(m_result, tuple):
                m_name = "F_" + str(m_index)
                tmp_fractions.update({m_name: m_result})
            elif isinstance(m_result, algebra.Matrix):
                m_name = "M_" + str(m_index)
                tmp_matrices.update({m_name: m_result})
            # update string_in_progress
            string_in_process[pos0] = m_name
            for idx in range(pos0 + 1, pos2 + 1):
                string_in_process[idx] = None
            # update latex_in_progress
            latex_in_process[pos0] = f'\\text{{{prefix[:-1]}}}'
            for idx in range(pos0 + 1, pos0 + len(prefix)):
                latex_in_process[idx] = ''
    return True, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions


def get_base_to_clean_power(input_string, string_in_process, latex_in_process, read_range,
                            matrices_dict, tmp_matrices, tmp_fractions,
                            brackets_all, brackets_opening, brackets_closing,
                            input_iteration, ending_index):
    # base can be a matrix, a fraction or an integer
    # matrix
    starting_index = \
        find_position_of_a_matrix_in_string(input_string, string_in_process, latex_in_process, read_range,
                                            matrices_dict, tmp_matrices, tmp_fractions,
                                            brackets_all, brackets_opening, brackets_closing,
                                            ending_index, True, input_iteration)
    if starting_index is not None:
        return starting_index, 'matrix'

    # integer
    starting_index = \
        find_position_of_an_integer_in_string(input_string, ending_index, True, tmp_fractions,
                                              string_in_process, latex_in_process)
    if starting_index is not None:
        return starting_index, 'number'

    # fraction / decimal
    starting_index = \
        find_position_of_a_fraction_in_string(input_string, string_in_process, latex_in_process, read_range,
                                              matrices_dict, tmp_matrices, tmp_fractions,
                                              brackets_all, brackets_opening, brackets_closing,
                                              ending_index, True, input_iteration)
    if starting_index is not None:
        return starting_index, 'number'

    return None, None


def get_exponent_to_clean_power(input_string, string_in_process, latex_in_process, read_range,
                                matrices_dict, tmp_matrices, tmp_fractions,
                                brackets_all, brackets_opening, brackets_closing,
                                input_iteration, starting_index):
    # exponent can be an integer or T / (T)
    if input_string[starting_index + 1:].startswith('T'):
        return starting_index + 2, 'transpose'
    if input_string[starting_index + 1:].startswith('(T)'):
        return starting_index + 4, 'transpose'

    ending_index = \
        find_position_of_an_integer_in_string(input_string, starting_index, False, tmp_fractions,
                                              string_in_process, latex_in_process)
    if ending_index is not None:
        return ending_index, 'number'

    if input_string[starting_index + 1] == '(':
        ending_index = \
            find_position_of_an_integer_in_string(input_string, starting_index + 1, False, tmp_fractions,
                                                  string_in_process, latex_in_process)
        if ending_index is not None and ending_index + 1 < len(input_string) and input_string[ending_index + 1] == ')':
            return ending_index + 1

    return None, None


def clean_powers(input_string, string_in_process, latex_in_process, read_range,
                 matrices_dict, tmp_matrices, tmp_fractions,
                 brackets_all, brackets_opening, brackets_closing,
                 input_iteration):
    """
    Deals with "^" in the input

    Args:
        input_string:
        string_in_process:
        latex_in_process:
        read_range:
        matrices_dict:
        tmp_matrices:
        tmp_fractions:
        brackets_all:
        brackets_opening:
        brackets_closing:
        input_iteration:

    Returns:

    """
    # 'base' of the power will be between pos_base0 and pos_base1
    # 'exponent' will be between pos_power0 and pos_power1
    m_result = m_name = None
    caret_indexes = [idx for idx, char in enumerate(input_string) if char == '^']
    for caret_index in caret_indexes:
        base_idx, base_type = get_base_to_clean_power(input_string, string_in_process, latex_in_process, read_range,
                                                      matrices_dict, tmp_matrices, tmp_fractions,
                                                      brackets_all, brackets_opening, brackets_closing,
                                                      input_iteration, caret_index)
        if base_idx is not None:
            exponent_idx, exponent_type = get_exponent_to_clean_power(input_string, string_in_process, latex_in_process,
                                                                      read_range,
                                                                      matrices_dict, tmp_matrices, tmp_fractions,
                                                                      brackets_all, brackets_opening, brackets_closing,
                                                                      input_iteration, caret_index)
        else:
            return False, 'incorrect power', latex_in_process, matrices_dict, tmp_matrices, tmp_fractions

    # acceptable cases:
    # base: fraction, exponent: integer
    # base: integer,  exponent: integer
    # base: matrix,   exponent: transpose
    # base: matrix,   exponent: integer

    # todo: use base and exponent
    while True:
        pos_base1 = input_string.rfind('^') - 1
        if pos_base1 == -2:
            return input_string, brackets_all, brackets_opening, brackets_closing
        pos_power0 = pos_base1 + 2
        # isolates exponent, which should be either T or (T) or (-1) or a positive integer
        # todo: M^(-2) should be understood as (M^-1)^2
        exponent = None
        pos_power1 = pos_power0
        if pos_power0 in brackets_opening:
            pos_power1 = brackets_all[brackets_opening.index(pos_power0)][1]
            if input_string[pos_power0 + 1: pos_power1] == "T":
                exponent = "T"
        else:
            if input_string[pos_power0] == "T":
                exponent = "T"
            else:
                if ord(input_string[pos_power1]) == ord("-"):
                    pos_power1 += 1
                while pos_power1 < len(input_string) and input_string[pos_power1].isdigit():
                    pos_power1 += 1
                pos_power1 -= 1
                if pos_power1 < pos_power0:
                    # it may be also an integer stored in tmp_fractions
                    if input_string[pos_power0:].startswith('F_'):
                        fraction_ending_index = \
                            algebra.find_last_index_of_a_digit_in_string_from_position(input_string,
                                                                                       pos_power0 + 2,
                                                                                       left=False)
                        if fraction_ending_index:
                            exponent = tmp_fractions.get(input_string[pos_power0: fraction_ending_index + 1], None)
                            exponent = exponent[0] if exponent[1] == 1 else None
                            if exponent:
                                input_string = input_string[:pos_power0] \
                                               + str(exponent) \
                                               + input_string[fraction_ending_index + 1:]
                                pos_power1 = pos_power0 + len(str(exponent)) - 1
                                brackets_all, brackets_opening, brackets_closing = get_pairs_of_brackets_from_string(input_string)
                    else:
                        return None
        if exponent is None:
            # power is not T, (T) nor (-1), it must be an integer then
            power_status, power_val, assign_ans = read_input(input_string[pos_power0: pos_power1 + 1],
                                                             matrices_dict,
                                                             tmp_matrices,
                                                             tmp_fractions,
                                                             input_iteration + 1)
            if isinstance(power_val, tuple) and power_val[1] == 1:
                exponent = power_val[0]
                try:
                    exponent = int(exponent)
                except Exception as e:
                    _logger.error('Incorrect power. {}'.format(e))
                    return None
        # isolates the base of the power
        if pos_base1 in brackets_closing:
            # base is an expression in brackets
            pos_base0 = brackets_all[brackets_closing.index(pos_base1)][0]
        else:
            pos_base0 = algebra.find_starting_index_of_matrix_name_in_string(input_string,
                                                                             matrices_dict,
                                                                             tmp_matrices,
                                                                             pos_base1 + 1)
            if pos_base0 == -1:
                # base is without brackets, it is not a matrix, so it must be a positive integer
                pos_base0 = pos_base1
                while pos_base0 >= 0 and input_string[pos_base0].isdigit():
                    pos_base0 -= 1
                pos_base0 += 1
                if pos_base0 > pos_base1:
                    return None
        base_status, base_val, assign_ans = read_input(input_string[pos_base0: pos_base1 + 1],
                                                       matrices_dict,
                                                       tmp_matrices,
                                                       tmp_fractions,
                                                       input_iteration + 1)
        if isinstance(base_val, tuple):
            if exponent < 0:
                base_val = (base_val[1], base_val[0])
                exponent = -exponent
            m_result = (1, 1)
            for _ in range(exponent):
                m_result = algebra.get_fraction_cancelled_down(m_result[0] * base_val[0], m_result[1] * base_val[1])
            m_name = "F_" + str(len(tmp_fractions))
            tmp_fractions.update({m_name: m_result})
        elif isinstance(base_val, algebra.Matrix):
            if exponent == "T":
                m_result = base_val.transpose()
            elif exponent == -1:
                m_result = base_val.inverse()
            elif exponent > 0:
                m_result = algebra.EmptyMatrix(base_val)
                m_result.identity()
                for _ in range(exponent):
                    m_result = m_result.multiply_matrix(base_val) if m_result else None
            if m_result:
                m_name = "M_" + str(len(tmp_matrices))
                tmp_matrices.update({m_name: m_result})
            else:
                return None
        else:
            return None

        num_spaces = pos_power1 - pos_base0 + 1 - len(m_name)
        if num_spaces >= 0:
            input_string = input_string[:pos_base0] + m_name + " " * num_spaces + input_string[pos_power1 + 1:]
        else:
            input_string = input_string[:pos_base0] + m_name + input_string[pos_power1 + 1:]
            brackets_all = get_pairs_of_brackets_from_string(input_string)
            if brackets_all is None:
                return None

    # return input_string, brackets, brackets_open, brackets_close


def get_string_from_dict(dict_to_convert, for_latex=False):
    # todo: this makes sense only for latex_in_process
    before, after = ('{', '}') if for_latex else ('', '')
    keys = list(dict_to_convert.keys())
    keys.sort()
    return_string = ''
    for key in keys:
        return_string += f'{before}{dict_to_convert[key][1]}{after}'
    return return_string


def read_input(input_string, string_in_process, latex_in_process, read_range,
               matrices_dict, tmp_matrices, tmp_fractions,
               brackets_all, brackets_opening, brackets_closing,
               input_iteration=0):
    """
    Args:
        input_string:
        string_in_process:
        latex_in_process:
        read_range:
        matrices_dict:
        tmp_matrices:
        tmp_fractions:
        brackets_all:
        brackets_opening:
        brackets_closing:
        input_iteration:

    Returns:
        is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions
    """
    is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
        read_input_within_brackets(input_string, string_in_process, latex_in_process,
                                   matrices_dict, tmp_matrices, tmp_fractions,
                                   brackets_all, brackets_opening, brackets_closing,
                                   input_iteration)
    if not is_outcome_valid:
        return is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions

    for prefix in ["AUG(", "SUB(", "RREF(", "REF(", "DET("]:
        is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions =\
            prefix_functions(prefix,
                             input_string, string_in_process, latex_in_process, read_range,
                             matrices_dict, tmp_matrices, tmp_fractions,
                             brackets_all, brackets_opening, brackets_closing,
                             input_iteration)
        if not is_outcome_valid:
            return is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions
    # todo: EARLY: clear numbers and change to tmp_fractions ???
    # todo: the rest goes here

    # todo: power
    # todo: splitting operations (+, -)
    # todo: splitting operations (*, /)
    # todo: simple object

    if input_iteration == 0:
        # change string_in_process, latex_in_process into proper strings
        string_in_process = get_string_from_dict(string_in_process)
        latex_in_process = get_string_from_dict(latex_in_process)
    return is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions


def restricted_chars_used(input_string):
    """Check if restricted characters are used in input_string.

    Args:
        input_string (str): A string to be searched through.
    Returns:
        restricted_char_used (bool),
        info message (str) - if True
    """
    for letter in input_string:
        if letter in {"=", "+", "-", "/", "*", "(", ")", "^", ".", ","} \
                or (ord("A") <= ord(letter) <= ord("Z")) or letter.isdigit():
            continue
        else:
            return True, f'Your input contains restricted character "{letter}".'
    return False, ''


def deal_with_simple_commands(input_string, matrices_dict):
    """Deals with commands that do not result in a matrix or a number.

    Args:
        input_string (str): User's input to be analyzed.
        matrices_dict:

    Returns:
        is_outcome_valid (bool) - True if query correct, False otherwise
        output_string (str) -   an answer to user 'query' LaTeXed and mathjax wrapped if is_outcome_valid,
                                or simple info string otherwise
        input_latexed (str) - user_input in LaTeXed and mathjax wrapped form if is_outcome_valid, else None
        refresh_storage (bool) - indicates whether the storage section of the main page is to be refreshed
    """
    if input_string.startswith('DEL'):
        # deleting a matrix
        if input_string.startswith('DEL(') and input_string.endswith(')'):
            m_name = input_string[4:-1]
        elif input_string.startswith('DEL'):
            m_name = input_string[3:]
        else:
            m_name = ''
        if m_name in matrices_dict:
            database.delete_matrix(m_name)
            return True, '\\text{Matrix deleted.}', f'\\text{{del}}{m_name}', True
        else:
            # or a few matrices
            terms = m_name.count(",") + 1
            if terms > 1:
                names_of_matrices_to_delete = m_name.split(',')
                correct_del_input = all([matrix in matrices_dict for matrix in names_of_matrices_to_delete])
                if correct_del_input:
                    for matrix in names_of_matrices_to_delete:
                        matrices = list(matrices_dict.values())
                        names = list(matrices_dict.keys())
                        ind = matrices.index(matrix)
                        database.delete_matrix(names[ind])
                    return True, "\\text{Matrices deleted.}", f'\\text{{del}}({m_name})', True
                else:
                    return False, 'Improper input of "del".', input_string, False
            return False, f'There is no matrix named {m_name} in the database.', f'\\text{{del}}({m_name})', False
    return None


def correct_matrix_name(matrix_name_as_string, matrices_dict):
    """
    Checks if matrix_name_as_string is a correct matrix name.

    Returns:
        True, '' - when correct, otherwise:
        False, a message to be displayed
    """
    # if matrix_name_as_string in matrices_dict:
    #     return False, 'The name is already in use.'

    m = re.compile(r'[A-Z]+[\d]*').match(matrix_name_as_string)
    if m is None or m.group(0) != matrix_name_as_string or len(matrix_name_as_string) > 5:
        return False, 'A matrix name should consist of letters that may be followed by digits ' \
                      'and it should not exceed 5 characters.'

    for word in {'DET', 'CLS', 'HELP', 'CREATE'}:
        if word in matrix_name_as_string:
            return False, f'A name cannot contain "{word}", it is a restricted word.'
    if matrix_name_as_string == 'T':
        return False, 'A name cannot be "T", it is a restricted word.'
    return True, ''


def get_input_read(user_input, matrices_dict):
    """
    Args:
        user_input:
        matrices_dict:

    Returns:
        output_string (str) -   an answer to user 'query' LaTeXed and mathjax wrapped if query correct,
                                or simple info string otherwise
        input_latexed (str) - if user_input can be processed, then this shows it in LaTeXed and mathjax wrapped form
        refresh_storage (bool) - indicates whether the storage section of the main page is to be refreshed
    """
    input_string = user_input.strip()

    restricted_char_found, message = restricted_chars_used(input_string)
    if restricted_char_found:
        return message, input_string, False

    input_string = get_signs_tidied_up(input_string)

    simple_command = deal_with_simple_commands(input_string, matrices_dict)
    if simple_command is not None:
        is_outcome_valid, output_string, input_latexed, refresh_storage = simple_command
        if is_outcome_valid:
            output_string = mathjax_wrap(output_string)
            input_latexed = mathjax_wrap(input_latexed)
        return output_string, input_latexed, refresh_storage

    equal_sign_index = input_string.find('=')
    potential_matrix_name = input_string[:equal_sign_index] if equal_sign_index > 0 else None
    if potential_matrix_name:
        is_correct, message = correct_matrix_name(potential_matrix_name, matrices_dict)
        if not is_correct:
            return message, input_string, False
    # now potential_matrix_name != None means that the outcome is to be stored

    input_string = get_brackets_simplified(input_string)
    if input_string is None:
        return 'unbalanced brackets', '', False
    latex_in_process = dict()
    string_in_process = dict()
    for i in range(len(input_string)):
        string_in_process[i] = None
        latex_in_process[i] = ''

    tmp_matrices = dict()
    tmp_fractions = dict()
    brackets_all, brackets_opening, brackets_closing = get_pairs_of_brackets_from_string(input_string)

    is_outcome_valid, string_in_process, latex_in_process, matrices_dict, tmp_matrices, tmp_fractions = \
        read_input(input_string, string_in_process, latex_in_process, (0, len(input_string)),
                   matrices_dict, tmp_matrices, tmp_fractions,
                   brackets_all, brackets_opening, brackets_closing,
                   0)

    # todo: finish
    return_string = ''
    refresh_storage = 0
    # if not is_outcome_valid:
    #     return_string = '\\text{I cannot perform the operation requested. Try again.}'
    # elif isinstance(result, str):
    #     return_string = result
    #     if 'Matrix deleted.' in return_string or 'Matrices deleted.' in return_string:
    #         refresh_storage = 1
    # else:
    #     if isinstance(result, algebra.Matrix):
    #         return_string = result.get_latex_form()
    #         if assign_answer[0]:  # answer is to be stored
    #             refresh_storage = 1
    #             matrices_dict.update({assign_answer[2]: result})
    #             if assign_answer[1]:  # answer is to overwrite an existing matrix
    #                 database.delete_matrix(assign_answer[2])
    #                 return_string += '\\text{{ The result was stored ' \
    #                                  'in the existing matrix }}{}.'.format(assign_answer[2])
    #             else:
    #                 return_string += '\\text{{ The result was stored in the new matrix }}{}.'.format(assign_answer[2])
    #             database.save_matrix(assign_answer[2], matrices_dict)
    #     elif isinstance(result, tuple):
    #         if result[1] == 1:
    #             return_string = str(result[0])
    #         else:
    #             return_string = '\\frac{{{}}}{{{}}}'.format(result[0], result[1])
    #         if assign_answer[0]:
    #             return_string += '\n\\text{, only matrices can be stored.}'

    return return_string, refresh_storage


def wrap_with_tag(text, tag, dom_elt_id=None, dom_elt_class=None):
    html_id = ' id=\'{}\''.format(dom_elt_id) if dom_elt_id else ''
    html_class = ' class=\'{}\''.format(dom_elt_class) if dom_elt_class else ''
    return f'<{tag}{html_id}{html_class}>{text}</{tag}>'


def get_html_from_table(table, dom_row_id=None, with_header=True):
    def get_table_row(row_content, row_id, row_tag='tr'):
        dom_this_row_id = f'{dom_row_id}{row_id}' if dom_row_id else None
        row_string = ''
        for cell_content in row_content:
            row_string += wrap_with_tag(cell_content, 'td')
        row_string = wrap_with_tag(row_string, row_tag, dom_this_row_id)
        return row_string

    if with_header:
        table_columns = table[0]
        table_rows = table[1:]
        table_header = ''
        # header row
        for cell_text in table_columns:
            table_header += wrap_with_tag(cell_text, 'th')
        table_header = wrap_with_tag(table_header, 'tr')
    else:
        table_rows = table
        table_header = None
    # other rows
    table_content = list()
    for idx, row in enumerate(table_rows):
        table_content.append(get_table_row(row, idx))

    return table_header, table_content


def get_matrix_help_command_menu_by_idx(idx):
    table = config.help_commands[idx][1:][0]
    header_none, html_table = get_html_from_table(table, with_header=False)
    return ''.join(html_table)


def get_matrix_help_command_menu_by_command(command):
    commands = [elt[0] for elt in config.help_commands]
    if command.upper() in commands:
        idx = commands.index(command.upper())
        return get_matrix_help_command_menu_by_idx(idx)
    return None


def get_matrix_help_general_menu():
    """Displays general help information."""
    table_header, table_content = get_html_from_table(config.help_general_info, 'help-row-')
    return config.help_general_intro, table_header, table_content


def matrix_help_command(help_command):
    """Displays help information for a single command.

    Args:
        help_command (str): A command that the user searches help about.

    Returns:
        empty string when the help info is displayed correctly,
        None otherwise.
    """
    help_commands = list()
    for elt in config.help_commands:
        help_commands.append(elt[0])
    if help_command in help_commands:
        our_line = config.help_commands[help_commands.index(help_command)]
        both_lists = [list(), list()]
        for i in [1, 2]:
            if isinstance(our_line[i], str):
                both_lists[i - 1] = [our_line[i]]
            elif isinstance(our_line[i], list):
                both_lists[i - 1] = our_line[i]
        list_command, list_action = both_lists[0], both_lists[1]
        max_lines = max(len(list_command), len(list_action))
        for _ in range(max_lines - len(list_command)):
            list_command.append("")
        for _ in range(max_lines - len(list_action)):
            list_action.append("")
        max_command, max_action = 0, 60
        for i in range(max_lines):
            if len(list_command[i]) > max_command:
                max_command = len(list_command[i])
        if max_command < len("commands"):
            max_command = len("commands")
        print("+" + "-" * (max_command + 2) + "+" + "-" * (max_action + 2) + "+")
        print("|" + " commands " + " " * (max_command - 8) + "|"
              + " action " + " " * (max_action - 6) + "|")
        print("+" + "-" * (max_command + 2) + "+" + "-" * (max_action + 2) + "+")
        for i in range(max_lines):
            print("| " + list_command[i] + " " * (max_command - len(list_command[i])) + " | ", end="")
            if len(list_action[i]) < max_action:
                print(list_action[i] + " " * (max_action - len(list_action[i])) + " |")
            else:
                print_list = list_action[i][:list_action[i][:max_action].rfind(" ")]
                print(print_list + " " * (max_action - len(print_list)) + " |")
                actions = list_action[i][len(print_list) + 1:].split()
                while True:
                    print_list = ""
                    while True:
                        if len(print_list) + len(actions[0]) > max_action:
                            break
                        print_list += actions.pop(0) + " "
                        if len(actions) == 0:
                            break
                    print("|" + " " * (max_command + 2) + "| "
                          + print_list + " " * (max_action - len(print_list)) + " |")
                    if len(actions) == 0:
                        break
        print("+" + "-" * (max_command + 2) + "+" + "-" * (max_action + 2) + "+")
        return ""
    else:
        return None


if __name__ == '__main__':
    string_list_0 = ['1.23', '-.9', '.98', '-12.34', '-12/45', '43/23', '-235', '23']
    string_list = list()
    for elt in string_list_0:
        string_list.append(f'aa{elt}a')
    for string in string_list:
        for starting_id, go_left in {(1, False), (len(string) - 1, True)}:
            print((string + '  ').ljust(12, '<'), 'L' if go_left else 'R', starting_id,
                  find_position_of_an_integer_in_string(string, starting_id, go_left, None))


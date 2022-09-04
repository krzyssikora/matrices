from matrices import database, algebra, config, utils
from matrices.config import _logger


def mathjax_wrap(ltx_string):
    return r'\( {} \)'.format(ltx_string)


def get_list_of_matrix_dict_latexed(m_dict):
    m_list = list()
    for name, matrix in m_dict.items():
        m_list.append((name, mathjax_wrap('{}={}'.format(name, matrix.get_latex_form()))))
    m_list.sort()
    return m_list


def find_tuple_in_list(list_of_tuples, search_value, which_coordinate=0, idx_from=None, idx_to=None):
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
        return find_tuple_in_list(list_of_tuples, search_value, which_coordinate, idx_mid, idx_to)
    elif pivot > search_value:
        return find_tuple_in_list(list_of_tuples, search_value, which_coordinate, idx_from, idx_mid)


def get_inner_pair_id(brackets, idx):
    start_pos, end_pos = brackets[idx]
    while True:
        idx += 1
        if idx >= len(brackets):
            return None
        if brackets[idx][1] < end_pos:
            return idx


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
            both_pos = find_tuple_in_list(brackets, start_pos)
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


def find_position_of_a_number_in_string(input_string, starting_id, go_left):
    # if o denotes a char with starting_id, we want to find
    # .....(...)o(...)......    or
    # .....11111o22222......
    #      ^   ^ ^   ^          if go_left is True / False
    #      T   T F   F
    def stop_condition(str_len, temp_id, go_l):
        ret_bool = (temp_id < 0) if go_l else (temp_id >= str_len)
        return ret_bool

    brackets = algebra.get_pairs_of_brackets_from_string(input_string)
    if brackets:
        if go_left:
            the_tuple = find_tuple_in_list(brackets, starting_id - 1, 1)
        else:
            the_tuple = find_tuple_in_list(brackets, starting_id + 1, 0)
        if the_tuple:
            return the_tuple[0], the_tuple[1] + 1

    shift = -1 if go_left else 1
    idx = starting_id
    while True:
        idx += shift
        if stop_condition(len(input_string), idx, go_left):
            break
        if not input_string[idx].isdigit():
            break

    if (idx - starting_id) * (-1 if go_left else 1) == 1:
        return None
    if go_left:
        return idx + 1, starting_id
    else:
        return starting_id + 1, idx


def insert_latex_fractions(input_string):
    while True:
        idx = input_string.find('/')
        if idx == -1:
            break
        id_before_start, id_before_end = find_position_of_a_number_in_string(input_string, idx, True)
        id_after_start, id_after_end = find_position_of_a_number_in_string(input_string, idx, False)
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


def other_brackets_collides_with_brackets(brackets, other_brackets):
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
            if other_brackets_collides_with_brackets(brackets[0], other_brackets[0]):
                return None

    for old, new in {('{', '('), ('}', ')'), ('[', '('), (']', ')')}:
        input_string = input_string.replace(old, new)

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


def read_input_within_brackets(input_string, brackets_all, matrices_dict, tmp_matrices, tmp_fractions, input_iteration):
    mutually_exclusive_brackets = get_mutually_exclusive_brackets(brackets_all)
    for opening_index, closing_index in mutually_exclusive_brackets:
        is_outcome_valid, output_string, input_latexed, output_value, assign_answer = \
            read_input(input_string, matrices_dict, tmp_matrices, tmp_fractions, input_iteration + 1)
        


def read_input(input_string, matrices_dict, tmp_matrices, tmp_fractions, input_iteration=0):
    assign_answer = [False, False, '']

    if input_iteration == 0:
        input_string = get_brackets_simplified(input_string)
        if input_string is None:
            return False, 'unbalanced brackets', None, None, assign_answer

    brackets_all, brackets_opening, brackets_closing = get_pairs_of_brackets_from_string(input_string)


    return is_outcome_valid, output_string, input_latexed, output_value, assign_answer


def get_input_read(user_input, matrices_dict):
    """

    Args:
        user_input:
        matrices_dict:

    Returns:
        output_string (str) -   an asnwer to user 'query' LaTeXed and mathjax wrapped if query correct,
                                or simple info string otherwise
        input_latexed (str) - if user_input can be processed, then this shows it in LaTeXed and mathjax wrapped form
        refresh_storage (bool) - indicates whether the storage section of the maon page is to be refreshed
    """
    tmp_matrices = dict()
    tmp_fractions = dict()
    is_outcome_valid, output_string, input_latexed, output_value, assign_answer = utils.read_input(user_input,
                                                                                                   matrices_dict,
                                                                                                   tmp_matrices,
                                                                                                   tmp_fractions,
                                                                                                   0)

    return_string = ''
    refresh_storage = 0
    if not is_outcome_valid:
        return_string = '\\text{I cannot perform the operation requested. Try again.}'
    elif isinstance(result, str):
        return_string = result
        if 'Matrix deleted.' in return_string or 'Matrices deleted.' in return_string:
            refresh_storage = 1
    else:
        if isinstance(result, algebra.Matrix):
            return_string = result.get_latex_form()
            if assign_answer[0]:  # answer is to be stored
                refresh_storage = 1
                matrices_dict.update({assign_answer[2]: result})
                if assign_answer[1]:  # answer is to overwrite an existing matrix
                    database.delete_matrix(assign_answer[2])
                    return_string += '\\text{{ The result was stored ' \
                                     'in the existing matrix }}{}.'.format(assign_answer[2])
                else:
                    return_string += '\\text{{ The result was stored in the new matrix }}{}.'.format(assign_answer[2])
                database.save_matrix(assign_answer[2], matrices_dict)
        elif isinstance(result, tuple):
            if result[1] == 1:
                return_string = str(result[0])
            else:
                return_string = '\\frac{{{}}}{{{}}}'.format(result[0], result[1])
            if assign_answer[0]:
                return_string += '\n\\text{, only matrices can be stored.}'

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
    for string in ['ref(z)', 'rref(z)', 'del(z)', 'aug(z)']:
        print(string, change_to_latex(string))

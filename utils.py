from matrices import database, algebra, config
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


def get_input_read(inp, matrices_dict):
    """Reads user's input and returns an adequate answer."""
    tmp_matrices = dict()
    tmp_fractions = dict()
    result_status, result, assign_answer = algebra.read_input(inp,
                                                              matrices_dict,
                                                              tmp_matrices,
                                                              tmp_fractions,
                                                              0)

    return_string = ''
    if not result_status:
        return_string = '\\text{I cannot perform the operation requested. Try again.}'
    elif isinstance(result, str):
        return_string = result
    else:
        if isinstance(result, algebra.Matrix):
            return_string = result.get_latex_form()
            if len(assign_answer) > 0 and assign_answer[0]:  # answer is to be stored
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

    return return_string


def matrix_help_general_menu():
    """Displays general help information."""
    # prints out a table with general help hints
    print("+--------------------+")
    print("| General help info. |")
    print("+--------------------+")
    print("This app offers various operations on matrices with rational inputs,")
    print("Let M and N be the names of matrices.")
    print("The following are the available actions.")
    print("To get more details type in a help command.")
    print()
    max_len = [0, 0, 0]
    for i in range(len(config.help_options)):
        for j in range(3):
            if len(config.help_options[i][j]) > max_len[j]:
                max_len[j] = len(config.help_options[i][j])

    max_len[0] += 2
    print("+" + "-" * (max_len[0] + 4) + "+" + "-" * (max_len[1] + 2) + "+" + "-" * (max_len[2] + 2) + "+")
    for i, line in enumerate(config.help_options):
        str_action = line[0]
        str_command = line[1]
        str_help = line[2]
        str_ast = "*" if (i != 0 and str_action != "") else " "
        print("| " + str_ast + " " + str_action + " " * (max_len[0] - len(str_action)) + " | "
              + str_command + " " * (max_len[1] - len(str_command))
              + " | " + str_help + " " * (max_len[2] - len(str_help)) + " | ")
        if i == 0:
            print("+" + "-" * (max_len[0] + 4) + "+" + "-" * (max_len[1] + 2) + "+" + "-" * (max_len[2] + 2) + "+")
    print("+" + "-" * (max_len[0] + 4) + "+" + "-" * (max_len[1] + 2) + "+" + "-" * (max_len[2] + 2) + "+")


def matrix_help_command(help_command):
    """Displays help information for a single command.

    Args:
        help_command (str): A command that the user searches help about.

    Returns:
        empty string when the help info is displayed correctly,
        None otherwise.
    """
    help_commands = list()
    for elt in config.help_explanations:
        help_commands.append(elt[0])
    if help_command in help_commands:
        our_line = config.help_explanations[help_commands.index(help_command)]
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

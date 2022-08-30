import math
from matrices.config import help_options, help_explanations
from matrices import database, utils, config
# from matrices import matrices_dict, matrices_str_dict, tmp_matrices, matrices_names, assign_answer
from matrices.config import _logger


def get_fraction_from_string(fraction_as_string):
    """Changes a string that represents a fraction into a tuple (numerator, denominator).

    Args:
        fraction_as_string (str): can be in a form of a decimal (e.g. "1.25"), a fraction ("34/56") or an integer.

    Returns:
        A tuple (numerator, denominator).

    Raises:
        Exception when the parameter is incorrect.
    """
    fraction_as_string = str(fraction_as_string)
    try:
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
        return numerator, den
    except Exception as e:
        _logger.debug(e)
        return None, None


def get_fractions_from_list_of_strings(list_of_fractions_as_strings):
    fractions = list()
    for fraction_as_string in list_of_fractions_as_strings:
        numerator, denominator = get_fraction_from_string(fraction_as_string)
        if numerator is None:
            return None
        fractions.append((numerator, denominator))
    return fractions


def get_fraction_cancelled_down(numerator, denominator):
    """Cancels a fraction down.

    Args:
        numerator (int): top of a fraction
        denominator (int): bottom of a fraction

    Returns:
        A tuple (top, bottom) representing the fraction cancelled down.
    """
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    divisor = math.gcd(numerator, denominator)
    if divisor == 1:
        return numerator, denominator
    else:
        return numerator // divisor, denominator // divisor


def get_sum_of_fractions(numerator_1, denominator_1, numerator_2, denominator_2):
    """Returns a sum of two fraction as a simplified fraction.

    Args:
        numerator_1 (int): top of the first fraction
        denominator_1 (int): bottom of the first fraction
        numerator_2 (int): top of the second fraction
        denominator_2 (int): bottom of the second fraction

    Returns:
        A tuple (top, bottom) representing the simplified sum of two fractions.
    """
    numerator_1, denominator_1 = get_fraction_cancelled_down(numerator_1, denominator_1)
    numerator_2, denominator_2 = get_fraction_cancelled_down(numerator_2, denominator_2)

    common_denominator = math.lcm(denominator_1, denominator_2)

    factor_1 = common_denominator // denominator_1
    factor_2 = common_denominator // denominator_2

    return get_fraction_cancelled_down(numerator_1 * factor_1 + numerator_2 * factor_2, common_denominator)


def find_starting_index_of_matrix_name_in_string(input_string, matrices_dict, tmp_matrices, position_after=None):
    """Finds a starting index of a matrix name.
    Checks for names in both matrices_dict and in tmp_matrices

    Args:
        tmp_matrices:
        matrices_dict:
        input_string (str): A string to be searched.
        position_after (int): An index just after the possible matrix name.

    Returns:
        The function returns the index of the starting character or -1 if a name is not found.
    """
    return_value = - 1
    if position_after is None:
        position_after = len(input_string)
    possible_index = position_after - 1
    while True:
        if possible_index < 0:
            break
        if input_string[possible_index: position_after] in matrices_dict:
            return_value = possible_index
            break
        if input_string[possible_index: position_after] in tmp_matrices:
            return_value = possible_index
            break
        possible_index -= 1
    return return_value


def get_pairs_of_brackets_from_string(input_string, opening_char="(", closing_char=")"):
    """Creates a list of pairs of positions of opening and closing brackets.

    Args:
        input_string (str): A string to be analyzed.
        opening_char (str): A character used for opening bracket.
        closing_char (str): A character used for closing bracket.

    Returns:
        A list of elements: [opening_index, closing_index] of pairs of indexes of opening and closed brackets.
        #todo check if changing list to a tuple may  produce any setbacks
    """
    ret = list()
    openings = list()
    closings = list()
    pos = -1
    # creates lists of positions of opening and closing brackets
    while True:
        pos = input_string.find(opening_char, pos + 1)
        if pos == -1:
            break
        openings.append(pos)
    while True:
        pos = input_string.find(closing_char, pos + 1)
        if pos == -1:
            break
        closings.append(pos)
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
            ret.append([opening, closing])
            openings.remove(opening)
            closings.remove(closing)
            ind -= 1
        else:
            ind += 1
    if len(closings) > 0:
        return None
    ret.sort()
    return ret


def correct_matrix_name(matrix_name_as_string, matrices_dict):
    # todo: redundant? Seems so, as implemented in JS, but also below in read_input.invalid_assignment_variable,
    #  but this can be easily refactored. Two ideas for this:
    #  1. add save button to results, below will not be needed (save numbers, too?)
    #  2. check if name in dicts, separately check if correct
    """Checks if matrix_name_as_string is a correct matrix name.

    Returns:
        True, "" - when correct, otherwise:
        False, a message to be displayed
    """
    if len(matrix_name_as_string) > 5:  # too long
        return False, "Maximum length of a name is 5 characters."
    if matrix_name_as_string in matrices_dict:  # already taken
        return False, "The name is already in use."
    letter_used = False
    digit_used = False
    # only letters and digits allowed, digits must follow letters
    for letter in matrix_name_as_string:
        if not letter_used and (ord("0") <= ord(letter) <= ord("9")):
            return False, "Letters must go before digits."
        if (ord("A") <= ord(letter) <= ord("Z")) and digit_used:
            return False, "Digits must not be placed before letters."
        if ord("A") <= ord(letter) <= ord("Z"):
            letter_used = True
        elif ord("0") <= ord(letter) <= ord("9"):
            digit_used = True
        else:
            return False, "Only letters and digits are allowed."
    for word in {"DET", "CLS", "HELP", "CREATE"}:
        if word in matrix_name_as_string:
            return False, "A name cannot contain \"" + word + "\", it is a reserved word."
    if matrix_name_as_string == "T":
        return False, "A name cannot be \"T\", it is a reserved word."
    return True, ""


def read_input(inp, matrices_dict, tmp_matrices, tmp_fractions, input_iteration=0):
    # todo REFACTOR
    """Changes the input (inp) into an answer - a matrix, a fraction (tuple) or None with an additional error message.

    Args:
        tmp_fractions:
        tmp_matrices:
        matrices_dict:
        inp (str): User's input to be analyzed.
        input_iteration (int): Shows the depth of recursion.
            (restricted characters are checked only for iteration = 0)
    """
    # todo: remove global variables
    # a few auxiliary functions

    def basics(input_string, matrices_dict):
        """Deals with commands that do not result in a matrix or a number.

        Args:
            matrices_dict:
            input_string (str): User's input to be analyzed.

        Returns:
            Either a string that will be proceed within read_input
            or a tuple (None, error_message (str))
        """
        if input_string == "CLS":
            return "c"
        elif input_string.startswith("DEL"):
            # deleting a matrix
            if input_string.startswith("DEL(") and input_string.endswith(")"):
                m_name = input_string[4:-1]
            elif input_string.startswith("DEL"):
                m_name = input_string[3:]
            else:
                m_name = ""
            if m_name in matrices_dict:
                database.delete_matrix(m_name)
                return ""
            else:
                # or a few matrices
                terms = m_name.count(",") + 1
                if terms > 1:
                    multiple_inp = multiple_input(m_name, terms)
                    if multiple_inp is None:
                        return None, '\\text{Improper input of "del".}'
                    if isinstance(multiple_inp, list):
                        for mat in multiple_inp:
                            if not isinstance(mat, Matrix):
                                return None, '\\text{Improper input of "del".}'
                        for mat in multiple_inp:
                            mats = list(matrices_dict.values())
                            names = list(matrices_dict.keys())
                            ind = mats.index(mat)
                            database.delete_matrix(names[ind])
                    return ""
                return None, f'\\text{{There is no matrix named }}' + m_name + '\\text{{ in the database.}}'
        elif input_string.startswith("HELP"):
            # todo: change it to displaying help message
            # displays help commands
            if len(input_string) == 4:
                utils.matrix_help_general_menu()
            else:
                help_command = input_string[4:]
                print("HELP COMMAND:", help_command)
                if utils.matrix_help_command(help_command) is None:
                    utils.matrix_help_general_menu()
                    return None, "Only help commands listed above can be used."
            return ""
        return None

    def restricted_chars_used(input_string, iteration=0):
        """Check if restricted characters are used in input_string.

        Args:
            input_string (str): A string to be searched through.
            iteration (int): the search is to be performed only in the initial part of the process (for iteration = 0),
            and not in the recursive repetitions (for iteration > 0).
        """
        if iteration == 0:
            for letter in input_string:
                if letter in {"=", "+", "-", "/", "*", "(", ")", "^", ".", ","} \
                        or (ord("A") <= ord(letter) <= ord("Z")) or (ord("0") <= ord(letter) <= ord("9")):
                    continue
                else:
                    print("Your input contains restricted character \"" + letter + "\".")
                    return True
        return False

    def invalid_assignment_variable(input_string, matrices_dict):
        """Checks if part before "=" of the user's input is a valid matrix name.

        It checks also, if the potential new name is already in use.
        The function changes the global variable assign answer, which is a list of three elements:
        0: assign (bool) - if True, answer should be stored, if False, the other two coordinates are irrelevant,
        1: overwrite (bool) - if True, answer overwrites an existing matrix,
        2: name of the new matrix
        """
        assign_answer = [False, False, '']
        if "=" in input_string:
            equal_sign_position = input_string.find("=")
            inp_new_variable = input_string[:equal_sign_position]
            correct, stderr = correct_matrix_name(inp_new_variable, matrices_dict)
            if "in use" in stderr:  # correct_matrix_name returns False, as the name is in use
                correct = True
            if correct:
                if inp_new_variable in matrices_dict:
                    assign_answer[1] = True  # answer is to overwrite an existing matrix
                assign_answer[2] = inp_new_variable
            else:
                return True, None
            assign_answer[0] = True  # answer must be stored
        return False, assign_answer

    def rearrange_spaces_and_brackets(input_string):
        """Removes spaces obtained from replacing parts of input with simplified expressions.

        Then it does bracketing again (i.e. recalls bracketing function and creates lists of opening brackets and
        closing brackets. Changes three global variables, as listed below.

        Args:
            input_string (str): A string to be searched through and simplified.

        Returns the simplified input_string.
        """
        nonlocal brackets, brackets_open, brackets_close
        input_string = input_string.replace(" ", "")
        brackets = get_pairs_of_brackets_from_string(input_string)
        if brackets is None:
            return None
        brackets_open = [x[0] for x in brackets]
        brackets_close = [x[1] for x in brackets]
        return input_string

    def remove_redundant_brackets(input_string):
        """Removes unnecessary brackets and does bracketing again.

        it does bracketing again (i.e. recalls bracketing function and creates lists of opening brackets and
        closing brackets. Changes three global variables, as listed below.

        Args:
            input_string (str): A string to be searched through and simplified.

        Returns simplified input string.
        """
        nonlocal brackets, brackets_open, brackets_close
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
        return rearrange_spaces_and_brackets(input_string)

    def multiple_input(input_string, number_of_parameters):
        """Returns a list of terms separated by commas.

        A term makes sense if it is a matrix or a tuple or a string.

        Args:
            input_string (str): A string to be searched through and simplified.
            number_of_parameters (int): The required number of terms to be found.
        Returns:
             None: if there is no way to split the input into terms making sense.
             A list of terms otherwise.
        """
        nonlocal brackets, brackets_open, brackets_close, input_iteration
        if number_of_parameters == 1:
            return_status, return_value, assign_ans = read_input(input_string,
                                                                 matrices_dict,
                                                                 tmp_matrices,
                                                                 tmp_fractions,
                                                                 input_iteration + 1)
            if not return_status:
                return None
            else:
                return [return_value]
        num_commas = input_string.count(",")
        if num_commas + 1 < number_of_parameters:
            return None
        pos = -1
        while True:
            pos = input_string.find(",", pos + 1)
            if pos == -1:
                return None
            # head is the part before the chosen comma
            head_status, head, assign_ans = read_input(input_string[:pos], matrices_dict, tmp_matrices, tmp_fractions, input_iteration + 1)
            # tail is the rest, split recursively
            tail = multiple_input(input_string[pos + 1:], number_of_parameters - 1)
            if not head_status or tail is None:
                continue
            elif isinstance(tail, tuple) and tail[0] is None:
                continue
            elif tail is not None:
                return_value = [head]
                return_value.extend(tail)
                return return_value
            break
        return None

    # TODO: documentation here
    # TODO: make it shorter
    def prefix_functions(input_string, pref, assign_answer):
        nonlocal brackets, brackets_open, brackets_close, input_iteration
        # replaces functions in the input (input_string) of the form: func(...)
        # where pref = "func("
        # with an appropriate result: tmp matrix's name or a tmp fraction's name
        # function del() is an exception, as it does not produce a result
        # that can be used to further calculations,
        # so it is dealt with in basics
        if input_string is None:
            return None
        m_result = m_name = None
        while True:
            pos0 = input_string.find(pref)
            if pos0 == -1:
                break
            pos1 = pos0 + len(pref) - 1
            if pos1 in brackets_open:
                # pos0 points to the first letter of pref,
                # pos1 to the opening bracket
                # pos2 to the closing bracket
                pos2 = brackets[brackets_open.index(pos1)][1]
                brackets.pop(brackets_open.index(pos1))
                brackets_close.pop(brackets_open.index(pos1))
                brackets_open.pop(brackets_open.index(pos1))
                # firstly functions that can have multiple inputs
                if pref in ["AUG(", "SUB(", "CREATE("]:
                    which_prefix = ["AUG(", "SUB(", "CREATE("].index(pref)
                    which_prefix += [2, 2, 0][which_prefix]
                    multiple_inp = multiple_input(input_string[pos1 + 1: pos2], which_prefix)
                    if multiple_inp is None and pref == "SUB(":
                        which_prefix += 2
                        multiple_inp = multiple_input(input_string[pos1 + 1: pos2], 5)
                    if multiple_inp is None:
                        return None
                    elif pref == "AUG(" and isinstance(multiple_inp, list) and isinstance(multiple_inp[0], Matrix) \
                            and isinstance(multiple_inp[1], Matrix):
                        m_result = multiple_inp[0].augment(multiple_inp[1])
                    elif pref == "SUB(":  # not resistant to mistakes
                        sub_inp = list()
                        for i in range(which_prefix - 1):
                            if isinstance(multiple_inp[1:][i], tuple):
                                sub_inp.append(multiple_inp[1:][i][0])
                            else:
                                return None
                        if isinstance(multiple_inp[0], Matrix):
                            m_result = multiple_inp[0].submatrix(*sub_inp)
                        else:
                            return None
                    elif pref == "CREATE(":
                        if isinstance(multiple_inp[0], tuple) and multiple_inp[0][1] == 1:
                            rows = multiple_inp[0][0]
                            try:
                                rows = int(rows)
                            except Exception as e:
                                print(e)
                                return None
                        else:
                            return None
                        if isinstance(multiple_inp[1], tuple) and multiple_inp[1][1] == 1:
                            columns = multiple_inp[1][0]
                            try:
                                columns = int(columns)
                            except Exception as e:
                                print(e)
                                return None
                        else:
                            return None
                        m_result = Matrix(rows, columns)
                        # todo: it was: m_result = Matrix(rows, columns, random_assignment=True)
                        if assign_answer[0]:
                            assign_answer[0] = False
                            print("Matrix " + assign_answer[2] + ":")
                            print(m_result)
                            matrices_dict.update({assign_answer[2]: m_result})
                            database.save_matrix(assign_answer[2])
                            assign_answer[2] = ""
                            if assign_answer[1]:
                                assign_answer[1] = False
                                print("has been changed.")
                            else:
                                print("has been created.")
                            return ""
                # then functions without an input
                else:
                    func_status, func_input, assign_ans = read_input(input_string[pos1 + 1: pos2],
                                                                     matrices_dict,
                                                                     tmp_matrices,
                                                                     tmp_fractions,
                                                                     input_iteration + 1)
                    if not func_status:
                        return None
                    elif isinstance(func_input, tuple):
                        return None  # argument of the function is a tuple
                    elif isinstance(func_input, Matrix):  # argument of the function is a matrix
                        list_prefixes = ["RREF(", "REF(", "DET("]
                        list_functions = [func_input.rref(), func_input.ref(), func_input.det()]
                        m_result = list_functions[list_prefixes.index(pref)]
                # replaces a part of the input with a tmp matrix or tmp fraction name
                m_ind = len(tmp_matrices)
                if m_result is None:
                    return None
                elif isinstance(m_result, tuple):  # SAME in read_input_recursively ???????
                    m_name = "F_" + str(m_ind)
                    tmp_fractions.update({m_name: m_result})
                elif isinstance(m_result, Matrix):
                    m_name = "M_" + str(m_ind)
                    tmp_matrices.update({m_name: m_result})
                num_spaces = pos2 - pos0 + 1 - len(m_name)
                if num_spaces >= 0:
                    input_string = input_string[:pos0] + m_name + " " * num_spaces + input_string[pos2 + 1:]
                else:
                    input_string = input_string[:pos0] + m_name + input_string[pos2 + 1:]
                    brackets = get_pairs_of_brackets_from_string(input_string)
                    if brackets is None:
                        return None
                    brackets_open = [x[0] for x in brackets]
                    brackets_close = [x[1] for x in brackets]
        return input_string

    # TODO: documentation here
    # TODO: make it shorter
    def power(input_string, matrices_dict, tmp_matrices):
        # deals with "^" in the input
        nonlocal brackets, brackets_open, brackets_close, input_iteration
        if input_string is None:
            return None
        # 'base' of the power will be between pos_base0 and pos_base1
        # 'exponent' will be between pos_power0 and pos_power1
        m_result = m_name = None
        while True:
            pos_base1 = input_string.find("^") - 1
            if pos_base1 == -2:
                return input_string
            pos_power0 = pos_base1 + 2
            # isolates exponent, which should be either T or (T) or (-1) or a positive integer
            exponent = None
            pos_power1 = pos_power0
            if pos_power0 in brackets_open:
                pos_power1 = brackets[brackets_open.index(pos_power0)][1]
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
            if pos_base1 in brackets_close:
                # base is an expression in brackets
                pos_base0 = brackets[brackets_close.index(pos_base1)][0]
            else:
                pos_base0 = find_starting_index_of_matrix_name_in_string(input_string,
                                                                         matrices_dict,
                                                                         tmp_matrices,
                                                                         pos_base1 + 1)
                if pos_base0 == -1:
                    # base is without brackets, it is not a matrix, so it must be a positive integer
                    pos_base0 = pos_base1
                    while pos_base0 >= 0 and ord("0") <= ord(input_string[pos_base0]) <= ord("9"):
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
                    m_result = get_fraction_cancelled_down(m_result[0] * base_val[0], m_result[1] * base_val[1])
                    m_name = "F_" + str(len(tmp_fractions))
                    tmp_fractions.update({m_name: m_result})
            elif isinstance(base_val, Matrix):
                if exponent == "T":
                    m_result = base_val.transpose()
                elif exponent == -1:
                    m_result = base_val.inverse()
                elif exponent > 0:
                    m_result = EmptyMatrix(base_val)
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
                brackets = get_pairs_of_brackets_from_string(inp)
                if brackets is None:
                    return None
                brackets_open = [x[0] for x in brackets]
                brackets_close = [x[1] for x in brackets]

    def read_input_recursively(input_string):
        """Splits the input into pieces of mutually exclusive brackets and reads input in each one of them.

        Args:
            input_string (str): A string to be searched through.

        Returns:
            simplified string, in which each expression in brackets is replaced with either a matrix name
            (from global matrices_dict, or a temporary one from tmp_matrices) or a temporary fraction name
            (from tmp_fractions).
        """
        nonlocal brackets, brackets_open, brackets_close, input_iteration
        brackets_mut_exc = list()
        ind = 0
        pivot = -1
        while True:
            if brackets[ind][0] > pivot:
                brackets_mut_exc.append(brackets[ind])
                pivot = brackets[ind][1]
            ind += 1
            if ind >= len(brackets):
                break
        brackets_mut_exc.sort(reverse=True)
        for elt in brackets_mut_exc:
            m_status, m_result, assign_ans = read_input(input_string[elt[0]: elt[1] + 1],
                                                        matrices_dict,
                                                        tmp_matrices,
                                                        tmp_fractions,
                                                        input_iteration + 1)
            m_name = None
            if not m_status:
                return None
            elif isinstance(m_result, tuple):
                m_name = "F_" + str(len(tmp_fractions))
                m_result = get_fraction_cancelled_down(m_result[0], m_result[1])
                tmp_fractions.update({m_name: m_result})
            elif isinstance(m_result, Matrix):
                m_name = "M_" + str(len(tmp_matrices))
                tmp_matrices.update({m_name: m_result})
            num_spaces = elt[1] - elt[0] + 1 - len(m_name)
            if num_spaces >= 0:
                input_string = input_string[:elt[0]] + m_name + " " * num_spaces + input_string[elt[1] + 1:]
            else:
                input_string = input_string[:elt[0]] + m_name + input_string[elt[1] + 1:]
                brackets = get_pairs_of_brackets_from_string(inp)
                if brackets is None:
                    return None
                brackets_open = [x[0] for x in brackets]
                brackets_close = [x[1] for x in brackets]
        return input_string

    # TODO: can this be made shorter ?
    def splitting_operations(input_string, operations):
        """Splits the input using the operations.

        Starts from right to ensure correct order of operations.
        Should be applied firstly for + and -, and then for * and /.

        Args:
            input_string (str): A string to analyze.
            operations (int):
                If operations = 0, the operations considered are + and -.
                If operations = 1, the operations considered are * and /.
        """
        nonlocal input_iteration
        if len(input_string) > 1:
            if input_string[0] == "+" and input_string[1] not in ["+", "-", "*", "/"]:
                input_string = input_string[1:]
        ops = [["+", "-"], ["*", "/"]]
        if input_string.count(ops[operations][0]) + input_string.count(ops[operations][1]) == 0:
            return inp
        last_operation_position = -1
        operation = None
        for op in ops[operations]:
            pos = input_string.rfind(op)
            if pos == -1:
                continue
            else:
                if pos > last_operation_position:
                    # addition: to accept inputs like "2/-3/4"
                    if operations == 0:
                        while pos > 0 and input_string[pos - 1] in ["*", "/"]:
                            pos = input_string.rfind(op, 0, pos)
                    if op == "-":
                        while pos > 0 and input_string[pos - 1] == "+":
                            pos = input_string.rfind(op, 0, pos)
                    if pos == -1:
                        continue
                    last_operation_position = pos
                    operation = op
        if last_operation_position >= 0:  # divide into smaller pieces
            m2_status, m2, assign_ans = read_input(input_string[last_operation_position + 1:],
                                                   matrices_dict,
                                                   tmp_matrices,
                                                   tmp_fractions,
                                                   input_iteration + 1)
            if last_operation_position == 0 and operation == "-":
                if isinstance(m2, Matrix):
                    m1 = EmptyMatrix(m2)
                    m1.zero_matrix()
                elif isinstance(m2, tuple):
                    m1 = (0, 1)
                else:
                    return None
                m1_status = True
            else:
                m1_status, m1, assign_ans = read_input(input_string[0: last_operation_position],
                                                       matrices_dict,
                                                       tmp_matrices,
                                                       tmp_fractions,
                                                       input_iteration + 1)
            if m1 is None or not m2_status or not m1_status:
                return None
            try:
                if (isinstance(m1, tuple) and m1[0] is None) or (isinstance(m2, tuple) and m2[0] is None):
                    return None
            except Exception as e:
                print(e)
            if isinstance(m1, Matrix) and isinstance(m2, Matrix):
                if operation == "+":
                    return m1.add_matrix(m2)
                elif operation == "-":
                    return m1.subtract_matrix(m2)
                elif operation == "*":
                    return m1.multiply_matrix(m2)
                else:
                    return None
            elif type(m1) == tuple and type(m2) == tuple:
                m10, m11, m20, m21 = int(m1[0]), int(m1[1]), int(m2[0]), int(m2[1])
                if operation == "+":
                    return get_sum_of_fractions(m10, m11, m20, m21)
                elif operation == "-":
                    return get_sum_of_fractions(m10, m11, -m20, m21)
                elif operation == "*":
                    return get_fraction_cancelled_down(m10 * m20, m11 * m21)
                elif operation == "/":
                    return get_fraction_cancelled_down(m10 * m21, m11 * m20)
                else:
                    return None
            elif isinstance(m1, Matrix) and type(m2) == tuple:
                if operation == "*":
                    return m1.multiply_scalar(m2[0], m2[1])
                else:
                    return None
            elif type(m1) == tuple and isinstance(m2, Matrix):
                if operation == "*":
                    return m2.multiply_scalar(m1[0], int(m1[1]))
                else:
                    return None
            else:
                return None
        return input_string

    def simple_object(input_string, matrices_dict):
        """Checks whether the input is a fraction or a matrix and returns a string with its name.

        The assumption here is that in the input string there are no more brackets, no more operations, so it must be
        either a matrix or a number.

        Args:
            matrices_dict:
            input_string (str): A string to be searched through.

        Returns:
            Either a matrix name (from matrices_dict or from tmp_matrices) or a fraction name (tmp_fractions) or
            None if the input does not make sense.
        """
        # matrix:
        if input_string in matrices_dict:
            return matrices_dict.get(input_string)
        elif input_string in tmp_matrices:
            return tmp_matrices.get(input_string)
        elif input_string in tmp_fractions:
            return tmp_fractions.get(input_string)
        else:  # a number, implemented as a tuple (numerator, denominator)
            try:
                num, den = get_fraction_from_string(input_string)
                if num is None:
                    return None
                else:
                    return num, den
            except Exception as e:
                print(e)
                return None

    assign_answer = [False, False, '']
    nothing_to_return = False, '', [False, False, '']
    inp = inp.upper().replace(" ", "")
    basic_output = basics(inp, matrices_dict)
    if basic_output is not None:
        return True, basic_output, assign_answer
    if restricted_chars_used(inp, input_iteration):
        return nothing_to_return
    invalid_assignment, assign_answer = invalid_assignment_variable(inp, matrices_dict)
    if invalid_assignment:
        return False, "New matrix name is incorrect.", assign_answer
    else:
        inp = inp[inp.find("=") + 1:]

    # the rest is for the part after "="
    brackets = get_pairs_of_brackets_from_string(inp)
    if brackets is None:
        return False, "Unbalanced brackets.", assign_answer
    inp = remove_redundant_brackets(inp)
    if inp is None:
        return False, "Brackets do not match.", assign_answer
    brackets_open = [x[0] for x in brackets]
    brackets_close = [x[1] for x in brackets]
    for prefix in ["AUG(", "SUB(", "RREF(", "REF(", "DET("]:
        inp = prefix_functions(inp, prefix, assign_answer)
        if inp is None:
            return False, f'\\text{{Improper input of "{{{prefix[:-1].lower()}}}".}}', assign_answer
        if inp == "":
            return True, "", assign_answer  # everything is fine, but all already done
    inp = rearrange_spaces_and_brackets(inp)
    inp = power(inp, matrices_dict, tmp_matrices)
    if inp is None:
        return False, "\\text{A power cannot be evaluated.}", assign_answer
    inp = rearrange_spaces_and_brackets(inp)
    if len(brackets) > 0:
        inp = read_input_recursively(inp)
    if inp is None:
        return nothing_to_return
    inp = splitting_operations(inp, 0)
    if not isinstance(inp, str):
        if inp is None:
            return nothing_to_return
        else:
            return True, inp, assign_answer
    inp = splitting_operations(inp, 1)
    if not isinstance(inp, str):
        return True, inp, assign_answer
    return True, simple_object(inp, matrices_dict), assign_answer


class Matrix:
    def __init__(self, rows=0, columns=0, values=None):
        """Initializes a matrix.

         A matrix is defined as a list of lists of numerators, the common denominator is stored separately.

         Args:
             rows (int): Number of rows of a matrix.
             columns (int): Number of columns of a matrix.
             values (list):
                either  tuples (numerator, denominator), the length must be = rows * columns
                or      list of rows, where each row as above
             otherwise they are entered by a user.
         """
        self.rows = rows
        self.columns = columns
        self.mat = list()
        self.denominator = 1
        denominators = list()

        if values is None:
            values = []

        # creating list of numerators (mat) and denominators
        arranged = (len(values) == rows)
        for r in range(rows):
            list_numerator = list()
            list_denominator = list()
            for c in range(columns):
                if arranged:
                    numerator, denominator = values[r][c]
                else:
                    numerator, denominator = values[r * columns + c]
                list_numerator.append(numerator)
                list_denominator.append(denominator)

            self.mat.append(list_numerator)
            denominators.append(list_denominator)

        # finding least common denominator
        for row in denominators:
            for denominator in row:
                if self.denominator // denominator == self.denominator / denominator:
                    continue
                else:
                    self.denominator = math.lcm(self.denominator, denominator)

        # adjusting numerators
        for row in range(rows):
            for column in range(columns):
                if denominators[row][column] == self.denominator:
                    continue
                else:
                    self.mat[row][column] = self.mat[row][column] * self.denominator // denominators[row][column]

    def __str__(self, output_form=None):
        """Returns a string showing the matrix.

        If a matrix is empty, its dimensions are displayed within curly braces, e.g. "{3x4}"

        Args:
            output_form (str):
                '' - simple notation,
                'wa' / 'wolframalpha - ready to paste into wolframalpha,
                'ltx' / 'latex', 'LaTeX' - LaTeX form
        """
        output_simple = {'', None}
        output_latex = {'ltx', 'latex', 'LaTeX'}
        output_wolframalpha = {'wa', 'wolframalpha', 'WolframAlpha'}
        if len(self.mat) == 0:
            return "{" + str(self.rows) + "x" + str(self.columns) + "}"
        # matrix_string - list of rows
        matrix_string = list()
        # max_columns_widths - list of max widths of columns
        max_columns_widths = [0 for _ in range(self.columns)]
        for row in range(self.rows):
            # row_string - list of strings from a row of the matrix
            row_string = list()
            for column in range(self.columns):
                # value_string - a string for a single cell of the matrix
                numerator, denominator = get_fraction_cancelled_down(self.mat[row][column], self.denominator)
                if denominator == 1:
                    value_string = str(numerator)
                elif numerator == 0:
                    value_string = "0"
                else:
                    if output_form in output_latex:
                        if numerator > 0:
                            sign = ''
                        else:
                            sign = '-'
                            numerator = -numerator
                        value_string = sign + '\\frac{{{}}}{{{}}}'.format(numerator, denominator)
                    else:
                        value_string = str(numerator) + "/" + str(denominator)
                if len(value_string) > max_columns_widths[column]:
                    max_columns_widths[column] = len(value_string)
                row_string.append(value_string)
            matrix_string.append(row_string)

        # make columns of even width if the matrix is to be printed in console
        if output_form in output_simple:
            for row in range(self.rows):
                for column in range(self.columns):
                    value_string = matrix_string[row][column]
                    if len(value_string) < max_columns_widths[column]:
                        matrix_string[row][column] = value_string.rjust(max_columns_widths[column])

        separator, beginning_of_row, end_of_row, beginning_of_matrix, end_of_matrix = None, None, None, None, None
        if output_form in output_simple:
            separator, beginning_of_row, end_of_row = " ", "[", "]\n"
            beginning_of_matrix, end_of_matrix = "[", "]"
        elif output_form in output_wolframalpha:
            separator, beginning_of_row, end_of_row = ", ", " [", "],\n"
            beginning_of_matrix, end_of_matrix = "[[", "]]"
        elif output_form in output_latex:
            separator, beginning_of_row, end_of_row = "& ", "", "\\\\ "
            beginning_of_matrix, end_of_matrix = r"\begin{pmatrix}", r"\end{pmatrix}"
        return_string = ""
        for row in range(self.rows):
            if row == 0:
                return_string += beginning_of_matrix
            else:
                return_string += beginning_of_row
            for column in range(self.columns):
                return_string = return_string + matrix_string[row][column]
                if column == self.columns - 1:
                    if row == self.rows - 1:
                        return_string += end_of_matrix
                    else:
                        return_string += end_of_row
                else:
                    return_string += separator
        return return_string

    def get_latex_form(self):
        return self.__str__(output_form='ltx')

    def get_wolframalpha_form(self):
        return self.__str__(output_form='wa')

    def simplify(self):
        """Simplifies the matrix.

        Finds a common factor for all entries and the denominator and divides all entries
        and the denominator by this factor.
        Changes the original matrix.
        """
        factor = -1
        for row in range(self.rows):
            for column in range(self.columns):
                divisor = math.gcd(self.mat[row][column], self.denominator)
                if factor == -1:
                    factor = divisor
                elif factor == 1:
                    continue
                else:
                    factor = math.gcd(divisor, factor)
        if factor > 1 or self.denominator < 0:
            if self.denominator < 0:
                factor *= -1
            self.denominator = self.denominator // factor
            for row in range(self.rows):
                for column in range(self.columns):
                    self.mat[row][column] = self.mat[row][column] // factor

    def multiply_scalar(self, top, bottom=1):
        """Multiplies the matrix by a scalar.

        Args:
            top, bottom (int): Top and bottom of the scalar as a fraction.

        Returns:
            The product of the matrix and the scalar as a fraction: top / bottom.
            """
        return_value = EmptyMatrix(self)
        if bottom < 0:
            top *= -1
            bottom *= -1
        top, bottom = get_fraction_cancelled_down(top, bottom)
        return_value.denominator = self.denominator * bottom
        for row in range(self.rows):
            row_list = list()
            for column in range(self.columns):
                row_list.append(self.mat[row][column] * top)
            return_value.mat.append(row_list)
        return_value.simplify()
        return return_value

    def add_matrix(self, another_matrix):
        """Returns a sum of the matrix and another_matrix."""
        if self.rows != another_matrix.rows or self.columns != another_matrix.columns:
            return None
        return_matrix = EmptyMatrix(self)
        for r in range(self.rows):
            return_matrix.mat.append(self.mat[r].copy())
        return_matrix = return_matrix.multiply_scalar(another_matrix.denominator)
        for row in range(self.rows):
            for column in range(self.columns):
                return_matrix.mat[row][column] += another_matrix.mat[row][column] * return_matrix.denominator
        return_matrix.denominator = return_matrix.denominator * another_matrix.denominator
        return_matrix.simplify()
        return return_matrix

    def subtract_matrix(self, another_matrix):
        """Returns a difference of the matrix and another_matrix."""
        return self.add_matrix(another_matrix.multiply_scalar(-1))

    def scalar_product(self, row, another_vector, another_vector_denominator=1):
        """Evaluates and returns a scalar product of two vectors, first being a row from the self matrix.

        Args:
            row (int): THe number of a row in the self matrix that is to be dot-multiplied.
            another_vector (Matrix or list): If a vector is given as a matrix, it should be just one row.
                If it is given as a list, then it is a list of numerators.
            another_vector_denominator (int): A common denominator for all numerators from another_vector.

        Returns:
            The scalar product as a tuple representing a fraction.
        """
        return_numerator, return_denominator = 0, 1
        self_vector = self.mat[row]
        self_vector_denominator = self.denominator
        if type(another_vector) == Matrix:
            another_vector_denominator = another_vector.denominator
            another_vector = another_vector.mat[0]
        for i in range(len(self_vector)):
            return_numerator, return_denominator = \
                get_sum_of_fractions(return_numerator, return_denominator, self_vector[i] * another_vector[i],
                                     self_vector_denominator * another_vector_denominator)
            return_numerator, return_denominator = get_fraction_cancelled_down(return_numerator, return_denominator)
        return return_numerator, return_denominator

    def det(self):
        """Returns the determinant of a square matrix."""
        if self.rows != self.columns:
            return None
        if self.rows == 1:
            return get_fraction_cancelled_down(self.mat[0][0], self.denominator)
        else:
            return_numerator, return_denominator = 0, 1
            for col in range(self.columns):
                det1, det2 = self.minor(0, col).det()
                new_numerator, new_denominator = \
                    get_fraction_cancelled_down(self.mat[0][col] * (-1) ** col * det1, self.denominator * det2)
                return_numerator, return_denominator = \
                    get_sum_of_fractions(return_numerator, return_denominator, new_numerator, new_denominator)
            return return_numerator, return_denominator

    def minor(self, row, column):
        """Returns the matrix with excluded row and column (both are indices - integers)."""
        return_matrix = EmptyMatrix(rows=self.rows - 1, columns=self.columns - 1)
        return_matrix.mat = list()
        return_matrix.denominator = self.denominator
        for r in range(self.rows):
            column_list = list()
            for c in range(self.columns):
                if row == r or column == c:
                    continue
                else:
                    column_list.append(self.mat[r][c])
            if r != row:
                return_matrix.mat.append(column_list)
        return return_matrix

    def transpose(self):
        """Returns the transpose of the matrix."""
        return_matrix = EmptyMatrix(rows=self.columns, columns=self.rows)
        return_matrix.denominator = self.denominator
        for column in range(self.columns):
            column_list = list()
            for row in range(self.rows):
                column_list.append(self.mat[row][column])
            return_matrix.mat.append(column_list)
        return return_matrix

    def inverse(self):
        """Returns the inverse of the matrix."""
        if self.rows != self.columns:
            return None
        if self.det() == 0:
            return None
        denominator = 1
        for row in range(self.rows):
            for column in range(self.rows):
                denominator = math.lcm(denominator, self.minor(row, column).det()[1])
        return_matrix = EmptyMatrix(self)
        return_matrix.denominator = denominator
        for row in range(self.rows):
            column_list = list()
            for column in range(self.rows):
                det_1, det_2 = self.minor(row, column).det()
                if det_2 != return_matrix.denominator:
                    det_1 = det_1 * return_matrix.denominator // det_2
                column_list.append(det_1 * (-1) ** (row + column))
            return_matrix.mat.append(column_list)
        return_matrix = return_matrix.transpose()
        det_1, det_2 = self.det()
        return_matrix = return_matrix.multiply_scalar(det_2, det_1)
        return return_matrix

    def multiply_matrix(self, another_matrix):
        """Returns the product of the matrix and another_matrix.

        Args:
            another_matrix (Matrix): The matrix to multiply the self matrix.
        """
        if self.columns != another_matrix.rows:
            return None
        return_matrix = EmptyMatrix(rows=self.rows, columns=another_matrix.columns)
        return_matrix.mat = [[0 for _ in range(return_matrix.columns)] for _ in range(return_matrix.rows)]
        return_matrix.denominator = self.denominator * another_matrix.denominator
        # evaluating elt [row][column]
        for row in range(return_matrix.rows):
            for column in range(return_matrix.columns):
                vector = list()
                for k in range(another_matrix.rows):
                    vector.append(another_matrix.mat[k][column])
                top, bottom = self.scalar_product(row, vector, another_matrix.denominator)
                if bottom == return_matrix.denominator:
                    return_matrix.mat[row][column] = top
                else:
                    return_matrix.mat[row][column] = top * return_matrix.denominator // bottom
        return return_matrix

    def find_non_zero(self, column=0, start_row=0):
        """Returns the number of the first row with non-zero entry in a given column.

        Args:
            column (int): column to be searched through.
            start_row (int): the position in the column where the search is to start.
        """
        for row in range(start_row, self.rows):
            if self.mat[row][column] != 0:
                return row
        return None

    def multiply_row(self, row_number, factor_top, factor_bottom):
        """Multiplies the row in the matrix by a fraction.

        Changes the matrix.

        Args:
            row_number (int): The number of a row to be multiplied by a fraction.
            factor_top (int): numerator of the fraction.
            factor_bottom (int): denominator of the fraction.
        """
        self.denominator = self.denominator * factor_bottom
        for column in range(self.columns):
            self.mat[row_number][column] = self.mat[row_number][column] * factor_top
        for row in range(self.rows):
            for column in range(self.columns):
                if row != row_number:
                    self.mat[row][column] = self.mat[row][column] * factor_bottom
        self.simplify()

    def row_add_row_multiplied(self, row_1, row_2, factor_top, factor_bottom):
        """Adds row with index row_2 multiplied by a fraction to row with index row_1.

        Changes the matrix.

        Args:
            row_1 (int): Index of a row to which another one is to be added.
            row_2 (int): Index of a row that is to be multiplied by a fraction and added to row_1.
            factor_top (int): numerator of the fraction.
            factor_bottom (int): denominator of the fraction.
        """
        self.denominator = self.denominator * factor_bottom
        for column in range(self.columns):
            self.mat[row_1][column] = self.mat[row_1][column] * factor_bottom + factor_top * self.mat[row_2][column]
        for row in range(self.rows):
            for column in range(self.columns):
                if row != row_1:
                    self.mat[row][column] = self.mat[row][column] * factor_bottom
        self.simplify()

    def swap_rows(self, row_1, row_2):
        """Swaps two rows of the matrix.

        Changes the matrix.

        Args:
            row_1, row_2 (int): Indices of rows to be swapped.
        """
        if row_1 > row_2:
            row_number_min = row_2
            row_number_max = row_1
        elif row_2 > row_1:
            row_number_min = row_1
            row_number_max = row_2
        else:
            return None
        row_max = self.mat.pop(row_number_max)
        row_min = self.mat.pop(row_number_min)
        self.mat.insert(row_number_min, row_max)
        self.mat.insert(row_number_max, row_min)

    def augment(self, another_matrix):
        """Returns the matrix augmented with another_matrix."""
        if self.rows != another_matrix.rows:
            return None
        return_matrix = EmptyMatrix(rows=self.rows, columns=self.columns + another_matrix.columns)
        return_matrix.denominator = math.lcm(self.denominator, another_matrix.denominator)
        factor_self = return_matrix.denominator // self.denominator
        factor_another = return_matrix.denominator // another_matrix.denominator
        for row in range(self.rows):
            column_list = list()
            for column in range(self.columns):
                column_list.append(self.mat[row][column] * factor_self)
            for column in range(another_matrix.columns):
                column_list.append(another_matrix.mat[row][column] * factor_another)
            return_matrix.mat.append(column_list)
        return return_matrix

    def submatrix(self, *rows_columns):
        """Finds and returns a sub-matrix of the self matrix.

        If 2 arguments are given (r, c),
            returns the matrix from row 1 to r inclusive and from column 1 to c inclusive.
        If 4 arguments given (r0, r1, c0, c1),
            returns the matrix from row r0 to r1 inclusive and from column c0 to c1 inclusive.
        """
        if len(rows_columns) == 2:
            first_row, last_row, first_column, last_column = 1, rows_columns[0], 1, rows_columns[1]
            if last_row == self.rows and last_column == self.columns:
                return self
        elif len(rows_columns) == 4:
            first_row, last_row, first_column, last_column \
                = rows_columns[0], rows_columns[1], rows_columns[2],  rows_columns[3]
        else:
            return None
        if last_row > self.rows:
            last_row = self.rows
        if last_column > self.columns:
            last_column = self.columns
        if last_row < first_row or last_column < first_column:
            return None
        return_matrix = EmptyMatrix(rows=last_row - first_row + 1, columns=last_column - first_column + 1)
        return_matrix.denominator = self.denominator
        for row in range(last_row - first_row + 1):
            column_list = list()
            for column in range(last_column - first_column + 1):
                cell_value = self.mat[first_row + row - 1][first_column + column - 1]
                column_list.append(cell_value)
            return_matrix.mat.append(column_list)
        return_matrix.simplify()
        return return_matrix

    def ref(self):
        """Returns row echelon form of the matrix."""
        return_matrix = EmptyMatrix(self)
        for r in range(self.rows):
            return_matrix.mat.append(self.mat[r].copy())
        stop = min(return_matrix.rows, return_matrix.columns)
        # make zeroes under diagonal
        for column in range(stop):
            # find pivot row
            row = return_matrix.find_non_zero(column, column)
            if row is None:
                continue
            elif row > column:
                return_matrix.swap_rows(row, column)
                row = column
            # make pivot = 1
            return_matrix.multiply_row(row, return_matrix.denominator, return_matrix.mat[row][column])
            # clear below pivot
            if column < return_matrix.rows - 1:
                for row in range(column + 1, return_matrix.rows):
                    factor_top, factor_bottom = get_fraction_cancelled_down(-return_matrix.mat[row][column],
                                                                            return_matrix.denominator)
                    return_matrix.row_add_row_multiplied(row, column, factor_top, factor_bottom)
        return_matrix.simplify()
        return return_matrix

    def rref(self):
        """Returns reduced row echelon form of the matrix."""
        return_matrix = self.ref()
        stop = min(return_matrix.rows, return_matrix.columns)
        for column in range(stop - 1, 0, -1):
            pivot_row = column
            while True:
                if return_matrix.mat[pivot_row][column] == 0:
                    pivot_row -= 1
                if return_matrix.mat[pivot_row][column] != 0 or pivot_row == 0:
                    break
            for row in range(pivot_row - 1, -1, -1):
                factor_top, factor_bottom = get_fraction_cancelled_down(-return_matrix.mat[row][column],
                                                                        return_matrix.denominator)
                return_matrix.row_add_row_multiplied(row, pivot_row, factor_top, factor_bottom)
            return_matrix.simplify()
        return return_matrix


class EmptyMatrix(Matrix):
    """An empty matrix that can be used to create or copy another one."""
    def __init__(self, matrix=None, rows=0, columns=0):
        """Initializes an empty matrix.

        It can be based either on a matrix passes as argument:
            then the empty matrix will have identical dimensions and the denominator,
        or on the number of rows and columns, then the denominator will be initially set to 1.
        """
        super().__init__()
        if matrix is None or matrix.mat is None or len(matrix.mat) == 0:
            self.rows = rows
            self.columns = columns
            self.denominator = 1
        else:
            self.rows = matrix.rows
            self.columns = matrix.columns
            self.denominator = matrix.denominator

    def identity(self):
        """Fills in an EmptyMatrix with identity matrix.

        Example of usage:
            3x3 identity:
            > mat1 = EmptyMatrix(Matrix(), 3, 3)
            > mat1.identity()
        """
        if self.rows == self.columns:
            self.denominator = 1
            self.mat = [[0 for _ in range(self.rows)] for _ in range(self.rows)]
            for i in range(self.rows):
                self.mat[i][i] = 1

    def zero_matrix(self):
        """Fills in an EmptyMatrix with zeroes.

        Example of usage:
            3x3 zero matrix:
            > mat1 = EmptyMatrix(Matrix(), 3, 3)
            > mat1.zero_matrix()
        """
        if self.rows == self.columns:
            self.denominator = 1
            self.mat = [[0 for _ in range(self.rows)] for _ in range(self.rows)]


if __name__ == '__main__':
    fracs = ['1.2', '2/-3', '-4/-3', '2/3', '', '4/14']
    matrix_vals = get_fractions_from_list_of_strings(fracs)
    print(matrix_vals)
    quit()
    matrix_vals = [matrix_vals[:3], matrix_vals[3:]]
    m = Matrix(2, 3, matrix_vals)
    print(m.get_latex_form())

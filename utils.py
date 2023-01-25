from matrices import database, algebra, config
import logging
import re
import inspect
import os
import copy

_logger = logging.getLogger('log.utils')


class StringTransformer:
    def __init__(self, input_string, matrices_dict):
        """
        An object whose parameters allow transformation of an input string from user
        into latex form and a processed answer.
        Args:
            input_string (str): from user
            matrices_dict (dict): items are (matrix name: algebra.Matrix object)
        """
        self.original_user_input = input_string
        self.input_string = input_string        # this will be changed, processed characters will be replaced
        self.matrices_dict = matrices_dict      # {name: algebra.Matrix}

        self.values_dict = dict()               # {idx from input: fraction (tuple) or algebra.Matrix}
        self.latex_dict = dict()                # {idx from input: part of LaTeX string}

        self.initial_brackets = None
        self.brackets = None                    # list of tuples (opening bracket, closing bracket)
        self.brackets_opening = None
        self.brackets_closing = None

        self.output_value = None                # algebra.Matrix if a result is a matrix, so it can be stored
        self.output_message = None              # message to be displayed when an input is incorrect
        self.input_latex = None                 # input transformed to LaTeX form
        self.correct_so_far = True              # when false, there is no sense to proceed
        self.refresh_storage = False            # True when input is of type 'name=...'

        self.potential_matrix_name = None       # a name to which the outcome value is to be assigned
        self.processed = False                  # True when input is processed and there is no need to continue

        self.past_versions = list()             # used for debugging, stores copies of self debug fields
        self.debug_fields = list()              # fields to be stored for debugging

        self.simplify_input_string()

    def all_debug_fields(self):
        return [
            ('self.input_string', self.input_string),
            ('self.values_dict', self.values_dict),
            ('self.latex_dict', self.latex_dict),
            ('self.brackets', self.brackets),
            ('self.output_message', self.output_message),
            ('self.output_value', self.output_value),
            ('self.input_latex', self.input_latex),
            ('self.correct_so_far', self.correct_so_far),
            ('self.refresh_storage', self.refresh_storage),
            ('self.potential_matrix_name', self.potential_matrix_name)
        ]

    def __str__(self):
        ret_string = '\n' + '-' * 50 + '\n'
        for ch in range(len(self.original_user_input)):
            ret_string += str(ch).rjust(3)
        ret_string += '\n'
        for elt in list(self.original_user_input):
            ret_string += elt.rjust(3)
        ret_string += '\n'
        for name, value in self.debug_fields:
            if value is not None:
                if isinstance(value, dict):
                    keys = list(value)
                    keys.sort()
                    for k in keys:
                        vst = str(value[k])
                        vst = vst.replace('\n', '\n' + ' ' * 31)
                        ret_string += f'{name.ljust(26)}: {str(k).ljust(3)}{vst}\n'
                else:
                    ret_string += f'{name.ljust(26)}: {value}\n'
        return ret_string

    def _get_indexes_before_and_after_from_values_and_latex(self, caret_index):
        """
        Args:
            caret_index: the position of a caret '^' in the input_string

        Returns:
            indexes of base and exponent in self.values_dict for evaluation of a power and
            indexes of start of base and end of exponent in self.latex_dict to place there curly braces '{', '}'
        """
        end = len(self.input_string)

        # get indexes for values
        indexes_from_values = list(self.values_dict)
        indexes_from_values.sort()
        indexes_from_values_before = [idx for idx in indexes_from_values if idx < caret_index]
        indexes_from_values_after = [idx for idx in indexes_from_values if idx > caret_index]
        values_base_idx = indexes_from_values_before[-1] if indexes_from_values_before else 0
        values_exponent_idx = indexes_from_values_after[0] if indexes_from_values_after else end

        indexes_from_latex = list(self.latex_dict)
        indexes_from_latex.sort()
        latex_keys_caret_index = indexes_from_latex.index(caret_index)
        # get opening index for latex
        latex_base_idx = indexes_from_latex[latex_keys_caret_index - 1]
        brackets = find_tuple_in_list_of_tuples_by_coordinate(self.initial_brackets, latex_base_idx, 1)
        if brackets:
            latex_base_idx = brackets[0]
        # get closing index for latex
        latex_exponent_idx = indexes_from_latex[latex_keys_caret_index + 1]
        while True:
            brackets = find_tuple_in_list_of_tuples_by_coordinate(self.initial_brackets, latex_exponent_idx, 0)
            if brackets is not None:
                latex_exponent_idx = brackets[1]
                # if latex_exponent_idx not in indexes_from_latex:
                #     break
            latex_keys_exponent_index = indexes_from_latex.index(latex_exponent_idx)
            if latex_keys_exponent_index < len(indexes_from_latex) - 1 and \
                    '^' in self.latex_dict.get(indexes_from_latex[latex_keys_exponent_index + 1], ''):
                latex_exponent_idx = indexes_from_latex[latex_keys_exponent_index + 2]
            else:
                break

        return values_base_idx, values_exponent_idx, latex_base_idx, latex_exponent_idx

    def debug(self, stack, intro_statement=''):
        debug_intro(stack)
        new_state = copy.deepcopy(self)
        new_state.past_versions = None
        new_state.debug_fields = None
        self.debug_fields = list()
        self.past_versions.append(new_state)
        if len(self.past_versions) <= 1:
            self.debug_fields = copy.deepcopy(self.all_debug_fields())
        else:
            old_state = self.past_versions[-2]
            for old, new in zip(old_state.all_debug_fields(), new_state.all_debug_fields()):
                if old[1] != new[1]:
                    self.debug_fields.append(new)
        _logger.debug(intro_statement + f'... {len(self.debug_fields)} changes from previous state')
        if self.debug_fields:
            _logger.debug(self)

    def get_signs_tidied_up(self):
        """
        Changes sequences of minuses and pluses in the input_string into one sign - a plus or a minus.
        """
        pos_0 = 0
        while True:
            if pos_0 >= len(self.input_string):
                break
            if self.input_string[pos_0] in {'+', '-'}:
                pos_1 = pos_0 + 1
                while True:
                    if pos_1 >= len(self.input_string) or self.input_string[pos_1] not in {'+', '-'}:
                        break
                    pos_1 += 1
                if pos_1 > pos_0 + 1:
                    pluses_and_minuses = self.input_string[pos_0: pos_1]
                    sgn = '-' if eval(pluses_and_minuses + '1') < 0 else '+'
                    self.input_string = self.input_string[:pos_0] + sgn + self.input_string[pos_1:]
            pos_0 += 1

    def deal_with_simple_commands(self):
        """Deals with commands that do not result in a matrix or a number.
        Returns:
            is_outcome_valid (bool) - True if query correct, False otherwise
            output_string (str) -   an answer to user 'query' LaTeXed and mathjax wrapped if is_outcome_valid,
                                    or simple info string otherwise
            input_latexed (str) - user_input in LaTeXed and mathjax wrapped form if is_outcome_valid, else None
            refresh_storage (bool) - indicates whether the storage section of the main page is to be refreshed
        """
        if self.input_string.startswith('DEL'):
            # deleting a matrix
            if self.input_string.startswith('DEL(') and self.input_string.endswith(')'):
                m_name = self.input_string[4:-1]
            elif self.input_string.startswith('DEL'):
                m_name = self.input_string[3:]
            else:
                m_name = ''
            if m_name in self.matrices_dict:
                database.delete_matrix(m_name)
                self.output_message = 'Matrix deleted.'
                self.latex_dict = {0: f'\\text{{del}}({m_name})'}
                self.refresh_storage = True
            else:
                # or a few matrices
                terms = m_name.count(",") + 1
                if terms > 1:
                    names_of_matrices_to_delete = m_name.split(',')
                    correct_del_input = all([matrix in self.matrices_dict for matrix in names_of_matrices_to_delete])
                    if correct_del_input:
                        for matrix_name in names_of_matrices_to_delete:
                            names = list(self.matrices_dict.keys())
                            ind = names.index(matrix_name)
                            database.delete_matrix(names[ind])
                        self.output_message = 'Matrices deleted.'
                        self.latex_dict = {0: f'\\text{{del}}({m_name})'}
                        self.refresh_storage = True
                    else:
                        self.correct_so_far = False
                        self.output_message = 'Improper input of "del".'
                        self.latex_dict = {0: self.input_string}
                        self.refresh_storage = False
                else:
                    self.correct_so_far = False
                    self.output_message = f'There is no matrix named {m_name} in the database.'
                    self.latex_dict = {0: f'\\text{{del}}({m_name})'}
                    self.refresh_storage = False
            return True  # which means it was a simple command
        return False  # it was not a simple command

    def get_numbers_and_matrices_from_string(self):
        """
        Replaces all positive integers or decimals in input_string with '#'.
        Replaces names of all stored matrices in input_string with '@'.
        Creates values_dict where:
            key: index of a matrix / number in updated input_string
            value: either algebra.Matrix object or a tuple (int, int)
        Exceptional case: for '^T' in the input_string, an item in values_dict is created:
            key: index of 'T'
            value: 'transpose'
        Updates:
            self.correct_so_far
            self.input_string
            self.values_dict
            self.latex_dict
        """

        def get_fraction_from_decimal_string(st):
            decimal_point_position = st.find('.')
            if decimal_point_position >= 0:
                return algebra.get_fraction_cancelled_down(int(st[:decimal_point_position] +
                                                               st[decimal_point_position + 1:]),
                                                           10 ** (len(st) - decimal_point_position - 1))
            else:
                return int(st), 1

        input_string = self.input_string
        matrices_dict = self.matrices_dict

        string_correct = True
        string_in_progress = input_string
        temporary_list = list()  # list of tuples (pos_0, pos_1, matrix / tuple)
        objects_dict = self.values_dict
        latex_dict = self.latex_dict

        # cover reserved words
        temporary_input_string = input_string
        for word in config.MATRIX_NAME_RESTRICTED_WORDS:
            temporary_input_string = temporary_input_string.replace(word, '_' * len(word))

        # collect matrices
        matrices_names = list(matrices_dict)
        matrices_names.sort(key=len, reverse=True)
        for matrix_name in matrices_names:
            while True:
                pos = temporary_input_string.find(matrix_name)
                if pos == -1:
                    break
                if pos - 1 >= 0 and temporary_input_string[pos - 1].isalpha():
                    string_correct = False
                    break
                if pos + len(matrix_name) < len(temporary_input_string) \
                        and temporary_input_string[pos + len(matrix_name)].isalpha():
                    string_correct = False
                    break

                if pos == 1 and temporary_input_string[0] == '-':
                    temporary_list.append(
                        (pos - 1, pos + len(matrix_name),
                         matrices_dict[matrix_name].multiply_scalar(-1),
                         len(matrix_name),
                         '-' + matrix_name))
                    temporary_input_string = \
                        temporary_input_string[:pos - 1] + '_' * (len(matrix_name) + 1) + temporary_input_string[
                                                                                pos + len(matrix_name):]
                else:
                    temporary_list.append((pos, pos + len(matrix_name),
                                           matrices_dict[matrix_name],
                                           len(matrix_name) - 1,
                                           matrix_name))
                    temporary_input_string = \
                        temporary_input_string[:pos] + '_' * len(matrix_name) + temporary_input_string[
                                                                                pos + len(matrix_name):]
        if not string_correct:
            self.correct_so_far = False
            self.input_string = input_string
            self.values_dict = objects_dict
            self.output_message = 'Incorrect input.'
            return

        # collect numbers
        pattern = re.compile(r'[\d]*[.]*[\d]*')
        previous_end = -1
        for m in pattern.finditer(temporary_input_string):
            pos_0, pos_1, object_string = m.start(), m.end(), m.group()
            if object_string and (('.' not in object_string) or ('.' in object_string and len(object_string) > 1)):
                if pos_0 <= previous_end:
                    string_correct = False
                    break
                previous_end = pos_1
                top, bottom = get_fraction_from_decimal_string(object_string)

                # check if there is a minus in front, i.e. the number is negative
                bare_minus_condition_met = \
                    (pos_0 == 1 and temporary_input_string[0] == '-') \
                    or (pos_0 > 1
                        and temporary_input_string[pos_0 - 1] == '-'
                        and temporary_input_string[pos_0 - 2] in {'^', '('})
                if bare_minus_condition_met:
                    temporary_list.append((pos_0 - 1, pos_1,
                                           (-top, bottom),
                                           len(object_string),
                                           '-' + object_string))
                else:
                    temporary_list.append((pos_0, pos_1,
                                           (top, bottom),
                                           len(object_string) - 1,
                                           object_string))
        if not string_correct:
            self.correct_so_far = False
            self.input_string = input_string
            self.values_dict = objects_dict
            self.output_message = 'Incorrect input.'
            return

        # make up a dictionary
        temporary_list.sort()
        shift = 0
        for pos_0, pos_1, target_object, delta_shift, object_string in temporary_list:
            pos_0 -= shift
            pos_1 -= shift
            replacement = '#' if isinstance(target_object, tuple) else '@'
            _logger.debug('pos_0: {}, pos_1: {}, target_object: {}, delta_shift: {}, object_string: {}'.format(
                pos_0, pos_1, type(target_object), delta_shift, object_string))
            _logger.debug('>>{},{},{}<<'.format(string_in_progress[:pos_0], replacement, string_in_progress[pos_1:]))
            objects_dict[pos_0] = target_object
            latex_dict[pos_0] = object_string
            string_in_progress = string_in_progress[:pos_0] + replacement + string_in_progress[pos_1:]
            shift += delta_shift
            _logger.debug('string_in_progress: {}'.format(string_in_progress))

        _logger.debug('input_string: {}'.format(input_string))
        _logger.debug('string_in_progress: {}'.format(string_in_progress))
        _logger.debug('objects_dict: {}'.format(objects_dict))
        _logger.debug('latex_dict: {}'.format(latex_dict))

        # add transposes to the dictionary
        caret_indexes = [idx for idx, char in enumerate(string_in_progress) if char == '^']
        for caret_index in caret_indexes:
            if caret_index in {0, len(self.input_string) - 1}:
                self.correct_so_far = False
                self.input_string = input_string
                self.values_dict = objects_dict
                return
            if string_in_progress[caret_index + 1] == 'T':
                objects_dict[caret_index + 1] = 'transpose'
                latex_dict[caret_index + 1] = 'T'

        self.correct_so_far = string_correct
        self.input_string = string_in_progress
        self.values_dict = objects_dict
        self.latex_dict = latex_dict
        return

    def simplify_input_string(self):
        """
        - checks whether the input contains restricted characters
        - checks if the string is a single command that does not produce an output (del M)
        - finds out if the output is to be stored and if the name of the new matrix is correct
        - simplifies brackets and stores them on self.brackets
        """
        restricted_char_found, message, escaped_string = restricted_chars_used(self.input_string)
        if restricted_char_found:
            self.output_message = message
            self.input_string = escaped_string
            self.correct_so_far = False
            return

        self.get_signs_tidied_up()
        if self.deal_with_simple_commands():
            if self.correct_so_far:
                self.output_message = mathjax_text_wrap(self.output_message)
                self.input_latex = mathjax_wrap(self.latex_dict[0])
                self.processed = True
        else:
            equal_sign_index = self.input_string.find('=')
            potential_matrix_name = self.input_string[:equal_sign_index] if equal_sign_index > 0 else None
            if potential_matrix_name:
                is_correct, message = correct_matrix_name(potential_matrix_name)
                if not is_correct:
                    self.output_message = message
                    self.latex_dict = {0: self.input_string}
                    self.correct_so_far = False
                elif potential_matrix_name not in self.matrices_dict:
                    self.potential_matrix_name = potential_matrix_name
                    self.refresh_storage = True
                    self.input_string = self.original_user_input[equal_sign_index + 1:]
                    self.latex_dict[-1] = potential_matrix_name + '='
                    self.simplify_input_string()
                    return
                else:
                    self.correct_so_far = False
                    self.output_message = 'The name is already in use. Delete the existing matrix first.'
                    self.input_latex = self.original_user_input
                    self.processed = True
                    return
            # now self.potential_matrix_name != None means that the outcome is to be stored
            _logger.debug('simplify_input_string, AFTER ===')
            _logger.debug('self.input_string: {}'.format(self.input_string))
            _logger.debug('self.values_dict: {}'.format(self.values_dict))
            _logger.debug('self.latex_dict: {}'.format(self.latex_dict))
            simplified_input_string = get_brackets_simplified(self.input_string)

            if simplified_input_string is None:
                self.output_message = 'Unbalanced brackets.'
                self.latex_dict = {0: self.input_string}
                self.correct_so_far = False
            else:
                self.input_string = simplified_input_string
                self.get_numbers_and_matrices_from_string()
                print(f'2: {self.correct_so_far}')
                _logger.debug('simplify_input_string, AFTER get_numbers_and_matrices_from_string')
                _logger.debug('self.input_string: {}'.format(self.input_string))
                _logger.debug('self.values_dict: {}'.format(self.values_dict))
                _logger.debug('self.latex_dict: {}'.format(self.latex_dict))
                self.brackets, self.brackets_opening, self.brackets_closing \
                    = get_pairs_of_brackets_from_string(self.input_string)
                self.initial_brackets = copy.deepcopy(self.brackets)

    def get_multiple_input_processed(self, read_range, input_iteration, number_of_parameters):
        """Inserts a list of terms separated by commas into string_in_progress.

        A term makes sense if it is a matrix or a tuple or a string.

        Args:
            read_range:
            input_iteration:
            number_of_parameters (int): The required number of terms to be found.

        Returns:
        """
        starting_position, ending_position = read_range
        _logger.debug(f'multiple: read_range: {read_range}, input_iteration: {input_iteration}, '
                      f'number_of_parameters: {number_of_parameters}')
        if number_of_parameters == 1:
            _logger.debug(f'...reading input from {inspect.stack()[0][3]}, 1 parameter')
            self.read_input(read_range, input_iteration)
            return

        num_commas = self.input_string[starting_position: ending_position].count(',')
        if num_commas + 1 < number_of_parameters:
            self.correct_so_far = False
            return
        pos = starting_position - 1
        while True:
            # find position of a comma that is not within any pair of brackets that are within the read_range
            brackets_within_range = \
                [bracket for bracket in self.brackets if bracket[0] >= read_range[0] and bracket[1] < read_range[1]]
            while True:
                pos = self.input_string[:ending_position].find(',', pos + 1)
                if pos == -1:
                    self.correct_so_far = False
                    return
                bracket = find_tuple_before_in_list_of_tuples_by_coordinate(list_of_tuples=brackets_within_range,
                                                                            search_value=pos,
                                                                            which_coordinate=0,
                                                                            # idx_from=starting_position,
                                                                            # idx_to=ending_position
                                                                            )
                if bracket is None or bracket[1] < pos:
                    break

            self.latex_dict[pos] = ','
            # head is the part before the chosen comma
            _logger.debug(f'...reading input from {inspect.stack()[0][3]}')
            self.read_input((starting_position, pos), input_iteration)
            head_correct = self.correct_so_far
            # tail is the rest, split recursively
            self.get_multiple_input_processed((pos + 1, ending_position),
                                              input_iteration + 1,
                                              number_of_parameters - 1)
            tail_correct = self.correct_so_far
            if not (head_correct and tail_correct):
                continue
            else:
                tail = self.values_dict[pos + 1]
                self.values_dict[starting_position] = \
                    [self.values_dict[starting_position]] + (tail if isinstance(tail, list) else [tail])
                self.correct_so_far = True
                return
        self.correct_so_far = False
        return

    def _set_attributes_when_input_incorrect(self, prefix):
        self.correct_so_far = False
        self.output_message = f'Incorrect input of "{prefix[:-1]}"'

    def prefix_functions(self, prefix, read_range, input_iteration):
        # deals with functions in the input_string of the form: func(...)
        # where prefix = "func("
        # inserts an appropriate result (tmp matrix's name or a tmp fraction's name) into string_in_progress

        starting_position, ending_position = read_range
        m_result = None
        while True:
            pos0 = self.input_string[:ending_position].find(prefix, starting_position)
            if pos0 == -1:
                break
            pos1 = pos0 + len(prefix) - 1
            _logger.debug('prefix: {}, self.input_string: {}, pos1: {}'.format(prefix, self.input_string, pos1))
            if pos1 < ending_position and pos1 in self.brackets_opening:
                # pos0 points to the first letter of prefix, pos1 and pos2 point to the opening and closing brackets
                pos2 = self.brackets[self.brackets_opening.index(pos1)][1]
                # firstly functions that can have multiple inputs
                if prefix in ["AUG(", "SUB(", "CREATE("]:
                    which_prefix = ["AUG(", "SUB(", "CREATE("].index(prefix)
                    number_of_parameters = which_prefix + [2, 2, 0][which_prefix]

                    self.get_multiple_input_processed((pos1 + 1, pos2), input_iteration, number_of_parameters)
                    if not self.correct_so_far and prefix == "SUB(":
                        self.correct_so_far = True
                        number_of_parameters += 2
                        self.get_multiple_input_processed((pos1 + 1, pos2), input_iteration, number_of_parameters)
                    multiple_input = self.values_dict[pos1 + 1]
                    if not self.correct_so_far:
                        self._set_attributes_when_input_incorrect(prefix)
                        return
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
                                self._set_attributes_when_input_incorrect(prefix)
                                return
                        if isinstance(multiple_input[0], algebra.Matrix):
                            m_result = multiple_input[0].submatrix(*sub_inp)
                        else:
                            self._set_attributes_when_input_incorrect(prefix)
                            return
                # then functions without an input
                else:
                    _logger.debug(f'...reading input from {inspect.stack()[0][3]}')
                    self.read_input((pos1 + 1, pos2), input_iteration + 1)
                    function_input = self.values_dict[pos1 + 1]
                    if not self.correct_so_far or isinstance(function_input, tuple):
                        self._set_attributes_when_input_incorrect(prefix)
                        return
                    elif isinstance(function_input, algebra.Matrix):  # argument of the function is a matrix
                        list_prefixes = ["RREF(", "REF(", "DET("]
                        list_functions = [function_input.rref(), function_input.ref(), function_input.det()]
                        m_result = list_functions[list_prefixes.index(prefix)]

                if m_result is None:
                    self._set_attributes_when_input_incorrect(prefix)
                    return

                self.values_dict[pos0] = m_result
                for idx in range(pos0 + 1, pos2 + 1):
                    if idx in self.values_dict:
                        self.values_dict.pop(idx)
                self.latex_dict[pos0] = f'\\text{{{prefix[:-1]}}}('
                self.latex_dict[pos2] = ')'
                for idx in range(pos0 + 1, pos0 + len(prefix)):
                    if idx in self.latex_dict:
                        self.latex_dict.pop(idx)
                # clean prefix in input_string
                self.input_string = \
                    self.input_string[:ending_position].replace(prefix[:-1], '_' * (len(prefix) - 1)) + \
                    self.input_string[ending_position:]
                # clean a comma in input_string
                self.input_string = \
                    self.input_string[:pos1] + \
                    self.input_string[pos1: pos2].replace(',', '_') + \
                    self.input_string[pos2:]
                self.brackets.remove((pos1, pos2))
                self.brackets_opening.remove(pos1)
                self.brackets_closing.remove(pos2)
        self.correct_so_far = True

    def read_input_within_brackets(self, read_range, input_iteration):
        starting_position, ending_position = read_range
        brackets_in_range = [(s, e) for (s, e) in self.brackets if
                             (s >= starting_position) and (e < ending_position)]
        mutually_exclusive_brackets = get_mutually_exclusive_brackets(brackets_in_range)

        _logger.debug(f'mutually_exclusive_brackets: {mutually_exclusive_brackets}')
        for opening_index, closing_index in mutually_exclusive_brackets:
            if opening_index == 0 or self.input_string[opening_index - 1] != '^':
                self.latex_dict[opening_index] = '{('
                self.latex_dict[closing_index] = ')}'
            elif not all(ch.isdigit() or ch == '.' for ch in self.input_string[opening_index + 2: closing_index]):
                self.latex_dict[opening_index] = '{('
                self.latex_dict[closing_index] = ')}'
            self.brackets.remove((opening_index, closing_index))
            self.input_string = self.input_string[:opening_index] + '_' + self.input_string[opening_index + 1:]
            self.input_string = self.input_string[:closing_index] + '_' + self.input_string[closing_index + 1:]
            _logger.debug(f'...reading input from {inspect.stack()[0][3]}, '
                          f'read_range: {(opening_index + 1, closing_index)}, '
                          f'input_iteration: {input_iteration}')
            self.read_input(read_range=(opening_index + 1, closing_index),
                            input_iteration=input_iteration + 1)
            if not self.correct_so_far:
                break
            if opening_index == 1 and self.input_string[0] == '-':
                # when minus is the very first character and is followed by '('
                outcome = self.values_dict[1]
                if isinstance(outcome, algebra.Matrix):
                    outcome = outcome.multiply_scalar(-1)
                elif isinstance(outcome, tuple):
                    outcome = (-outcome[0], outcome[1])
                self.values_dict[0] = outcome
                if 1 in self.values_dict:
                    self.values_dict.pop(1)

    def clean_powers(self, read_range):
        """
        Deals with "^" in the input.
        """
        # 'base' of the power will be between pos_base0 and pos_base1
        # 'exponent' will be between pos_power0 and pos_power1
        def set_attributes_when_incorrect(message=None):
            self.correct_so_far = False
            self.output_message = message if message else 'A power cannot be evaluated.'

        starting_position, ending_position = read_range

        _logger.debug(f'clean_powers, read_range: {read_range}')
        caret_indexes = [idx for idx, char in enumerate(self.input_string) if char == '^'
                         and idx in range(starting_position, ending_position)]
        caret_indexes.sort(reverse=True)
        for caret_index in caret_indexes:
            if self.input_string[starting_position: ending_position].count('^') > 0:
                self.debug(inspect.stack(), 'inside powers, read_range: {}'.format(read_range))
            if caret_index in {0, len(self.input_string) - 1}:
                return set_attributes_when_incorrect()

            self.latex_dict[caret_index] = '}^{'
            indexes = self._get_indexes_before_and_after_from_values_and_latex(caret_index)
            if indexes:
                values_base_idx, values_exponent_idx, latex_base_idx, latex_exponent_idx = indexes
            else:
                return set_attributes_when_incorrect()

            exponent_value = self.values_dict[values_exponent_idx]
            base_value = self.values_dict[values_base_idx]

            self.latex_dict[latex_base_idx] = '{{' + self.latex_dict.get(latex_base_idx, '')
            self.latex_dict[latex_exponent_idx] = self.latex_dict.get(latex_exponent_idx, '') + '}}'

            # case: ...^-integer
            if values_exponent_idx == caret_index + 2 and self.input_string[caret_index + 1] == '-':
                if isinstance(exponent_value, tuple):
                    exponent_value = (-exponent_value[0], exponent_value[1])
                    self.values_dict[values_exponent_idx] = exponent_value
                else:
                    return set_attributes_when_incorrect()

            # acceptable cases:
            # 1. base: matrix,   exponent: transpose
            # 2. base: matrix,   exponent: integer
            # 3. base: number,  exponent: integer
            if exponent_value == 'transpose' and isinstance(base_value, algebra.Matrix):
                # 1. base: matrix,   exponent: transpose
                new_value = base_value.transpose()
                self.input_string = \
                    self.input_string[:values_exponent_idx] + '_' + self.input_string[values_exponent_idx + 1:]
            elif isinstance(exponent_value, tuple) and exponent_value[1] == 1:
                if isinstance(base_value, algebra.Matrix):
                    # 2. base: integer,  exponent: integer
                    new_value = base_value.raise_matrix_to_a_power(exponent_value[0])
                    if new_value is None:
                        return set_attributes_when_incorrect('The inverse does not exist.')
                elif isinstance(base_value, tuple):
                    # 3. base: number,  exponent: integer
                    new_value = algebra.get_fraction_raised_to_power(base_value[0], base_value[1], exponent_value[0])
                else:
                    return set_attributes_when_incorrect()
            else:
                return set_attributes_when_incorrect()

            if new_value is None:
                return set_attributes_when_incorrect()
            # introduce new value into values_dict
            for idx in range(values_base_idx, values_exponent_idx + 1):
                if idx in self.values_dict:
                    self.values_dict.pop(idx)
            self.values_dict[values_base_idx] = new_value
            self.input_string = self.input_string[:caret_index] + '_' + self.input_string[caret_index + 1:]

    def split_input_by_operations(self, operations, read_range, input_iteration):
        """Splits the input using the operations.

        Starts from right to ensure correct order of operations.
        Should be applied firstly for + and -, and then for * and /.

        Args:
            operations (int):
                If operations = 0, the operations considered are + and -.
                If operations = 1, the operations considered are * and /.
            read_range:
            input_iteration:
        """
        def set_attributes_when_incorrect():
            self.correct_so_far = False
            self.output_message = 'The operation cannot be performed.'
            return

        initial_position, final_position = read_range
        _logger.debug('entering split method, read_range: {}'.format(read_range))
        ops = [['+', '-'], ['*', '/']]
        _logger.debug('initial_position: {}, final_position: {}, operations: {}, input_string: {}'.format(
            initial_position,
            final_position,
            operations,
            '_' * initial_position + self.input_string[initial_position:final_position]
            + '_' * (len(self.input_string) - final_position)))
        if self.input_string[initial_position:final_position].count(ops[operations][0]) \
                + self.input_string[initial_position:final_position].count(ops[operations][1]) == 0:
            return
        last_operation_position = -1
        operation = None
        for op in ops[operations]:
            pos = self.input_string.rfind(op, initial_position, final_position)
            if pos == -1:
                continue
            if pos > last_operation_position and initial_position < pos < final_position:
                # addition: to accept inputs like "2/-3/4"
                if operations == 0:
                    while pos > 0 and self.input_string[pos - 1] in ['*', '/']:
                        pos = self.input_string.rfind(op, initial_position, pos)
                if pos == -1:
                    continue
                last_operation_position = pos
                operation = op
        _logger.debug('last_operation_position before starting split: {}'.format(last_operation_position))
        if initial_position < last_operation_position < final_position - 1:  # divide into smaller pieces
            self.input_string = \
                self.input_string[:last_operation_position] + '_' + self.input_string[last_operation_position + 1:]
            _logger.debug('split started: {}<{}<{}'.format(
                initial_position, last_operation_position, final_position - 1))

            self.debug(inspect.stack(), 'read_range: {}-{}'.format(last_operation_position + 1, final_position))

            self.read_input((last_operation_position + 1, final_position),
                            input_iteration + 1)
            m2_status = self.correct_so_far
            if m2_status:
                m2 = self.values_dict[last_operation_position + 1]
            else:
                return set_attributes_when_incorrect()
            _logger.debug('results m2: {}, {}'.format(m2_status, m2))

            _logger.debug('read_range: {}-{}'.format(initial_position, last_operation_position))
            _logger.debug(f'...reading input from {inspect.stack()[0][3]}')
            self.read_input((initial_position, last_operation_position), input_iteration + 1)
            m1_status = self.correct_so_far
            if m1_status:
                m1 = self.values_dict[initial_position]
            else:
                return set_attributes_when_incorrect()
            _logger.debug('results m1: {}, {}'.format(m1_status, m1))

            if isinstance(m1, algebra.Matrix) and isinstance(m2, algebra.Matrix):
                if operation == "+":
                    return_value = m1.add_matrix(m2)
                    self.latex_dict[last_operation_position] = '+'
                elif operation == "-":
                    return_value = m1.subtract_matrix(m2)
                    self.latex_dict[last_operation_position] = '-'
                elif operation == "*":
                    return_value = m1.multiply_matrix(m2)
                    self.latex_dict[last_operation_position] = '\\times '
                else:
                    return set_attributes_when_incorrect()
            elif isinstance(m1, tuple) and isinstance(m2, tuple):
                m10, m11, m20, m21 = int(m1[0]), int(m1[1]), int(m2[0]), int(m2[1])
                if operation == '+':
                    return_value = algebra.get_sum_of_fractions(m10, m11, m20, m21)
                    self.latex_dict[last_operation_position] = '+'
                elif operation == '-':
                    return_value = algebra.get_sum_of_fractions(m10, m11, -m20, m21)
                    self.latex_dict[last_operation_position] = '-'
                elif operation == '*':
                    return_value = algebra.get_fraction_cancelled_down(m10 * m20, m11 * m21)
                    self.latex_dict[last_operation_position] = '\\times '
                elif operation == '/':
                    return_value = algebra.get_product_of_fractions(m10, m11, m21, m20)
                    if return_value is None:
                        self.output_message = 'Division by 0.'
                        self.correct_so_far = False
                        return
                    _logger.debug('BEFORE FRAC: {}'.format(self.latex_dict))
                    self.latex_dict[last_operation_position] = '}{'
                    self.latex_dict[initial_position] = \
                        '\\frac{' + self.latex_dict[initial_position] \
                        if initial_position in self.latex_dict else '\\frac{'
                    self.latex_dict[final_position - 1] = \
                        self.latex_dict[final_position - 1] + '}' if (final_position - 1) in self.latex_dict else '}'
                    _logger.debug('AFTER FRAC: {}'.format(self.latex_dict))
                else:
                    return set_attributes_when_incorrect()
            elif isinstance(m1, algebra.Matrix) and isinstance(m2, tuple):
                if operation == '*':
                    return_value = m1.multiply_scalar(m2[0], m2[1])
                    self.latex_dict[last_operation_position] = '\\times '
                elif operation == '/':
                    return_value = m1.multiply_scalar(m2[1], m2[0])
                    self.latex_dict[last_operation_position] = '\\div'
                else:
                    return set_attributes_when_incorrect()
            elif isinstance(m1, tuple) and isinstance(m2, algebra.Matrix):
                if operation == '*':
                    return_value = m2.multiply_scalar(m1[0], int(m1[1]))
                else:
                    return set_attributes_when_incorrect()
            else:
                return set_attributes_when_incorrect()
            if return_value:
                left_idx, right_idx = get_ids_before_and_after_in_dict(self.values_dict, last_operation_position)
                _logger.debug('self.values_dict: {}'.format(self.values_dict))
                _logger.debug('cleaning values for: {}, left: {}, right: {}'.format(last_operation_position, left_idx,
                                                                                    right_idx))
                for idx in {left_idx, right_idx}:
                    if idx in self.values_dict:
                        self.values_dict.pop(idx)
                self.values_dict[initial_position] = return_value
            else:
                return set_attributes_when_incorrect()

            self.debug(inspect.stack(), 'done')

    def no_more_chars_to_process_in_string(self, read_range):
        chars_to_remove = ['(', ')', '#', '@', '_']
        idx_from, idx_to = read_range
        chars = list(self.input_string[idx_from: idx_to])
        for char in chars_to_remove:
            while True:
                if char in chars:
                    chars.remove(char)
                else:
                    break
        return len(chars) == 0

    def there_is_exactly_one_value_in_range(self, read_range):
        keys = list(self.values_dict)
        start, end = read_range
        keys_in_range = [key for key in keys if start <= key < end]
        if len(keys_in_range) == 1:
            return True
        else:
            _logger.error('inappropriate values in the dict: {}'.format(self.values_dict))
            return False

    def read_input(self, read_range, input_iteration=0):
        self.debug(inspect.stack(),
                   'INITIALLY read_range: {}, input_iteration: {}'.format(read_range, input_iteration))
        start, end = read_range
        if end - start == 1:
            if input_iteration == 0:
                if len(self.values_dict) == 0:
                    self.output_message = 'Incorrect input.'
                    self.correct_so_far = False
                    return
                self.output_message = get_string_from_dict(self.values_dict)
                self.input_latex = get_latex_from_dict(self.latex_dict)
                self.output_value = self.values_dict.get(min(list(self.values_dict)) if self.values_dict else 0, '')
                self.debug(inspect.stack(),
                           'returning...read_range: {}, input_iteration: {}'.format(read_range, input_iteration))
            return

        if self.no_more_chars_to_process_in_string(read_range):
            this_range_result = None
            for idx in range(start, end):
                if idx in self.values_dict:
                    if this_range_result is None:
                        this_range_result = self.values_dict[idx]
                        self.values_dict.pop(idx)
                    else:
                        _logger.error(f'Result already retrieved: {this_range_result}, '
                                      f'new one: {self.values_dict[idx]} at {idx}.')
            if this_range_result:
                _logger.debug(f'no more characters to process in the range : {read_range}')
                self.values_dict[start] = this_range_result
                return
            else:
                _logger.error(f'No result found in the range: {read_range}')
        self.debug(inspect.stack(), 'read_range: {}, input_iteration: {}'.format(read_range, input_iteration))

        for prefix in ["AUG(", "SUB(", "RREF(", "REF(", "DET("]:
            self.prefix_functions(prefix, read_range, input_iteration)
            if not self.correct_so_far:
                return

        self.debug(inspect.stack(),
                   'AFTER PREFIX read_range: {}, input_iteration: {}'.format(read_range, input_iteration))

        if input_iteration >= 0:
            self.read_input_within_brackets(read_range, input_iteration)
        if not self.correct_so_far:
            return

        self.debug(inspect.stack(),
                   'AFTER BRACKETS read_range: {}, input_iteration: {}'.format(read_range, input_iteration))

        self.clean_powers(read_range)
        self.debug(inspect.stack(),
                   'AFTER POWERS read_range: {}, input_iteration: {}'.format(read_range, input_iteration))
        if not self.correct_so_far:
            return

        self.split_input_by_operations(0, read_range, input_iteration)
        if not self.correct_so_far:
            return

        self.debug(inspect.stack(),
                   'AFTER SPLIT 0 read_range: {}, input_iteration: {}'.format(read_range, input_iteration))

        self.split_input_by_operations(1, read_range, input_iteration)
        if not self.correct_so_far:
            return

        self.debug(inspect.stack(),
                   'AFTER SPLIT 1 read_range: {}, input_iteration: {}'.format(read_range, input_iteration))

        # there should be exactly one key of values_dict in the read_range or at 0
        # and NO chars to take care of in the range
        if self.correct_so_far:
            _logger.debug(f'>>> read_range: {read_range}, values_dicts.keys: {self.values_dict.keys()}')
            self.correct_so_far = \
                self.there_is_exactly_one_value_in_range(read_range) and \
                self.no_more_chars_to_process_in_string(read_range)

        if input_iteration == 0:
            if self.correct_so_far:
                _logger.debug('self.values_dict: {}'.format(self.values_dict))
                _logger.debug('self.latex_dict: {}'.format(self.latex_dict))
                self.output_message = get_string_from_dict(self.values_dict)
                self.input_latex = get_latex_from_dict(self.latex_dict)
                self.output_value = self.values_dict.get(min(list(self.values_dict)) if self.values_dict else 0, None)
            else:
                self.output_message = 'Incorrect input.'

        self.debug(inspect.stack(), 'FINALLY read_range: {}, input_iteration: {}'.format(read_range, input_iteration))


def mathjax_wrap(ltx_string):
    """
    Args:
        ltx_string:
    Returns:
        ltx_string wrapped with 'backslash opening_bracket', 'backslash closing_bracket'
        to make it recognizable by Math Jax
    """
    return r'\( {} \)'.format(ltx_string)


def mathjax_text_wrap(text_string):
    return r'\(\text{{{}}}\)'.format(text_string)


def get_list_of_matrix_dict_latexed(m_dict):
    """
    Args:
        m_dict: dictionary (matrix name : matrix object)
    Returns:
        a list of mathjax-wrapped strings of the form 'matrix name = matrix in LaTeX form'
    """
    m_list = list()
    for name, matrix in m_dict.items():
        m_list.append((name, mathjax_wrap('{}={}'.format(name, matrix.get_latex_form()))))
    m_list.sort()
    return m_list


def get_ids_before_and_after_in_dict(the_dict, idx):
    """
    Args:
        the_dict: its keys must be numbers
        idx: index to refer to
    Returns:
        largest key before and smallest after (or None-s)
    """
    i = 0
    left_idx, right_idx = None, None
    keys = list(the_dict)
    keys.sort()
    while True:
        if i >= len(keys):
            break
        if keys[i] > idx:
            if i > 0:
                left_idx, right_idx = keys[i - 1], keys[i]
            break
        i += 1

    return left_idx, right_idx


def find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples, search_value, which_coordinate=0, idx_from=None,
                                               idx_to=None):
    # todo: redundant?
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
    else:
        idx_to -= 1

    if idx_to < idx_from:
        return None

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
        return find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples,
                                                          search_value,
                                                          which_coordinate,
                                                          idx_mid,
                                                          idx_to + 1)
    elif pivot > search_value:
        return find_tuple_in_list_of_tuples_by_coordinate(list_of_tuples,
                                                          search_value,
                                                          which_coordinate,
                                                          idx_from,
                                                          idx_mid + 1)


def find_tuple_before_in_list_of_tuples_by_coordinate(list_of_tuples, search_value, which_coordinate=0, idx_from=None,
                                                      idx_to=None):
    """
    binary search of a tuple whose certain coordinate is less than search_value
    Args:
        list_of_tuples:
        search_value:
        which_coordinate:
        idx_from:
        idx_to:
    Returns:
        The tuple with which_coordinate largest but less than search_value
        or None if there is no such tuple.
    """
    list_of_tuples.sort()
    if idx_from is None:
        idx_from = 0
    if idx_to is None:
        idx_to = len(list_of_tuples) - 1
    else:
        idx_to -= 1

    if idx_to < idx_from:
        return None

    if idx_from == idx_to or idx_to - idx_from == 1:
        if list_of_tuples[idx_from][which_coordinate] < search_value:
            return list_of_tuples[idx_from]
        elif list_of_tuples[idx_to][which_coordinate] < search_value:
            return list_of_tuples[idx_to]
        else:
            return None

    idx_mid = (idx_from + idx_to) // 2
    try:
        pivot = list_of_tuples[idx_mid][which_coordinate]
        if pivot < search_value:
            return find_tuple_before_in_list_of_tuples_by_coordinate(list_of_tuples,
                                                                     search_value,
                                                                     which_coordinate,
                                                                     idx_mid,
                                                                     idx_to + 1)
        elif pivot >= search_value:
            return find_tuple_before_in_list_of_tuples_by_coordinate(list_of_tuples,
                                                                     search_value,
                                                                     which_coordinate,
                                                                     idx_from,
                                                                     idx_mid + 1)
    except Exception as e:
        _logger.error('*' * 20 + ' ERROR ' + '*' * 20)
        _logger.error(f'{e}')
        _logger.error('list_of_tuples: {}, search_value: {}, which_coordinate: {}, idx_from: {}, idx_to: {}'.format(
            list_of_tuples, search_value, which_coordinate, idx_from, idx_to))
        _logger.error('idx_mid: {}'.format(idx_mid))

        raise


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
            new_brackets.append((elt[0], elt[1]))
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

    # remove initial and final brackets
    while True:
        brackets, brackets_open, brackets_close = get_pairs_of_brackets_from_string(input_string)
        if brackets is None:
            return None
        if (0, len(input_string) - 1) in brackets:
            input_string = input_string[1:-1]
        else:
            break
    # brackets, brackets_open, brackets_close = get_pairs_of_brackets_from_string(input_string)
    # if brackets is None:
    #     return None
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

    all_brackets = [brackets_round, brackets_square, brackets_curly]
    for brackets in all_brackets:
        all_other_brackets = [b for b in all_brackets if b != brackets]
        for other_brackets in all_other_brackets:
            if other_brackets_collide_with_brackets(brackets[0], other_brackets[0]):
                return None

    for old, new in {('{', '('), ('}', ')'), ('[', '('), (']', ')')}:
        input_string = input_string.replace(old, new)

    brackets = get_pairs_of_brackets_from_string(input_string)
    input_string, brackets, brackets_open, brackets_close = remove_redundant_brackets(input_string, brackets[0])
    _logger.debug('simplifying brackets, input_string: {}, brackets: {}, brackets_open: {}, brackets_close: {}'.format(
        input_string, brackets, brackets_open, brackets_close))
    return input_string


def get_mutually_exclusive_brackets(brackets):
    if len(brackets) == 0:
        return []
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


def get_string_from_dict(dict_to_convert):
    keys = list(dict_to_convert.keys())
    keys.sort()
    return_string = ''
    for key in keys:
        value = dict_to_convert[key]
        if isinstance(value, tuple):
            new_value = str(value[0]) if value[1] == 1 else f'\\frac{{{value[0]}}}{{{value[1]}}}'
        elif isinstance(value, algebra.Matrix):
            new_value = value.get_latex_form()
        elif value is None:
            return 'Incorrect input.'
        else:
            new_value = f'>>{str(value)}<<'
        return_string += new_value
    return return_string


def get_latex_from_dict(dict_to_convert):
    # before, after = '{', '}'
    before, after = '', ''
    keys = list(dict_to_convert)
    keys.sort(reverse=True)
    chars_not_to_be_surrounded = ['{', '}', '(', ')', '^', '+', '-', '*', '/']
    # chars_in_strings_not_to_be_surrounded = ['^']  # ['^', '+', '-', '*', '/']
    return_string = ''
    for key in keys:
        latex_string = dict_to_convert[key]
        if latex_string:
            return_string = \
                (latex_string + return_string) \
                if any(latex_string.startswith(char) for char in chars_not_to_be_surrounded) \
                else (f'{before}{latex_string}{after}' + return_string)
        # if not any(return_string.startswith(char) for char in chars_in_strings_not_to_be_surrounded) \
        #         and not any(char in return_string for char in {'(', ')'}):
        #     return_string = f'{before}{return_string}{after}'
        _logger.debug('key: {}, latex_string: {}, return_string: {}'.format(key, latex_string.rjust(5), return_string))
    return return_string


def restricted_chars_used(input_string):
    """Check if restricted characters are used in input_string.

    Args:
        input_string (str): A string to be searched through.
    Returns:
        restricted_char_used (bool),
        info message (str) - if True
    """
    restricted_char = False
    restricted_chars_in_string = list()
    restricted_chars_escaped = list()
    for idx, letter in enumerate(input_string):
        if letter in {"=", "+", "-", "/", "*", "(", ")", "^", ".", ","} \
                or (ord("A") <= ord(letter) <= ord("Z")) or letter.isdigit():
            continue
        else:
            restricted_char = True
            restricted_chars_in_string.append(letter)
            if letter in {'_'}:
                letter = '\\' + letter
            restricted_chars_escaped.append(letter)
    if restricted_char:
        insert_str = \
            f' "{restricted_chars_escaped[0]}"' if len(restricted_chars_escaped) == 1 \
            else 's \"{}\"'.format("\", \"".join(restricted_chars_escaped))
        return_string = f'Your input contains restricted character{insert_str}.'
        for letter, letter_escaped in zip(restricted_chars_in_string, restricted_chars_escaped):
            input_string = input_string.replace(letter, letter_escaped)
    else:
        return_string = ''
    return restricted_char, return_string, input_string


def correct_matrix_name(matrix_name_as_string):
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


def get_values_for_js_matrix(list_of_rows, denominator):
    single_list = list()
    for row in list_of_rows:
        single_list += row
    values = list()
    for elt in single_list:
        num, den = algebra.get_fraction_cancelled_down(elt, denominator)
        den = str(den)
        values.append((f'minussign{str(-num)}' if elt < 0 else str(num)) + 'slashsign' + den)
    return values


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
        saveable (bool) - can the output be saved as a matrix
        output_value (algebra.Matrix) - the value to be saved when clicked
    """
    user_input = user_input.replace(' ', '')
    try:
        transformer = StringTransformer(input_string=user_input.strip(),
                                        matrices_dict=matrices_dict,
                                        )
        transformer.debug(inspect.stack(), 'BEFORE read_input')
        if transformer.processed:
            return mathjax_text_wrap(transformer.output_message), \
                   transformer.input_latex, \
                   transformer.refresh_storage, False, None

        if not transformer.correct_so_far:
            return mathjax_text_wrap(transformer.output_message), \
                   mathjax_text_wrap(transformer.latex_dict.get(0, transformer.input_string)), \
                   transformer.refresh_storage, False, None
        transformer.read_input(read_range=(0, len(transformer.input_string)), input_iteration=0)

        saveable = False
        output_value = transformer.output_value
        if transformer.correct_so_far:
            input_processed = mathjax_wrap(transformer.output_message)
            input_latexed = mathjax_wrap(transformer.input_latex)
            if isinstance(transformer.output_value, algebra.Matrix):
                saveable = True
                output_value = {
                    'name': '',
                    'rows': output_value.rows,
                    'columns': output_value.columns,
                    'values': get_values_for_js_matrix(output_value.mat, output_value.denominator)
                }
            if transformer.potential_matrix_name:
                refresh_storage = 1
                keys = list(transformer.values_dict)
                if len(keys) != 1:
                    _logger.error(f'to many values in dict: {transformer.values_dict}')
                    return mathjax_text_wrap('error'), \
                        mathjax_text_wrap(transformer.original_user_input), \
                        False, False, ''
                the_key = keys[0]
                if not isinstance(transformer.values_dict[the_key], algebra.Matrix):
                    return mathjax_text_wrap('Only matrices can be saved.'), \
                           mathjax_text_wrap(transformer.original_user_input), False, \
                           False, None
                _logger.debug(f'saving matrix {transformer.potential_matrix_name}')
                matrices_dict[transformer.potential_matrix_name] = transformer.values_dict[0]
                database.save_matrix(transformer.potential_matrix_name, matrices_dict)
            else:
                refresh_storage = 0
        else:
            input_processed = mathjax_text_wrap(transformer.output_message)
            input_latexed = transformer.original_user_input
            refresh_storage = 0
    except Exception as e:
        input_processed = mathjax_text_wrap('Incorrect input.')
        input_latexed = user_input
        refresh_storage = False
        saveable = False
        output_value = None
        _logger.error('an error occurred. {}'.format(e))

    return input_processed, input_latexed, refresh_storage, saveable, output_value


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


def debug_intro(inspect_stack):
    """
    0 - frame
    1 - file
    2 - line number
    3 - method
    4 - the line itself
    Args:
        inspect_stack: should be equal to inspect.stack()
    Returns:

    """
    stack = inspect_stack[0]
    file_name = os.path.basename(stack[1])
    line_number = stack[2]
    # line_content = stack[4][0].strip()
    method_name = stack[3]
    _logger.debug(f'>> {file_name}, {method_name}, line: {line_number}')


if __name__ == '__main__':
    pass

# FOR TESTS:
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


# todo: tests (?)

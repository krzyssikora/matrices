import math
from matrices import database
import logging

_logger = logging.getLogger('log.algebra')


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
        _logger.error(f'fraction error: {e}')
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


def get_product_of_fractions(numerator_1, denominator_1, numerator_2, denominator_2):
    """Returns a product of two fraction as a simplified fraction.

        Args:
            numerator_1 (int): top of the first fraction
            denominator_1 (int): bottom of the first fraction
            numerator_2 (int): top of the second fraction
            denominator_2 (int): bottom of the second fraction

        Returns:
            A tuple (top, bottom) representing the simplified product of two fractions.
    """
    num, den = get_fraction_cancelled_down(numerator_1 * numerator_2, denominator_1 * denominator_2)
    if den:
        return num, den
    else:
        return None


def get_fraction_raised_to_power(numerator, denominator, exponent):
    if int(exponent) != exponent:
        return None
    if exponent == 0:
        return 1, 0
    numerator, denominator = get_fraction_cancelled_down(numerator, denominator)
    if exponent < 0:
        exponent *= -1
        numerator, denominator = denominator, numerator

    return numerator ** exponent, denominator ** exponent


def get_pairs_of_brackets_from_string(input_string, opening_char="(", closing_char=")"):
    """Creates a list of pairs of positions of opening and closing brackets.

    Args:
        input_string (str): A string to be parsed.
        opening_char (str): A character used for opening bracket.
        closing_char (str): A character used for closing bracket.

    Returns:
        A list of elements: [opening_index, closing_index] of pairs of indexes of opening and closed brackets.
        #todo check if changing list to a tuple may  produce any setbacks
    """
    ret = list()
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
            ret.append([opening, closing])
            openings.remove(opening)
            closings.remove(closing)
            ind = max(0, ind - 1)
        else:
            ind += 1
        print(ind)
    if len(closings) > 0:
        return None
    ret.sort()
    return ret


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
        arranged = (len(values) == rows and rows > 1 and columns != 1)
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

    def __eq__(self, other):
        return str(self) == str(other)

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
        if self.det()[0] == 0:
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

    def raise_matrix_to_a_power(self, exponent):
        if self.columns != self.rows:
            return None
        if int(exponent) != exponent:
            return None

        return_value = EmptyMatrix(self)
        return_value.identity()
        if exponent == 0:
            return return_value
        elif exponent < 0:
            exponent *= -1
            multiplier = self.inverse()
        else:
            multiplier = self

        if multiplier is None:
            return None
        _logger.debug('multiplier: {}, exponent: {}'.format(multiplier, exponent))
        for _ in range(exponent):
            return_value = return_value.multiply_matrix(multiplier)

        return return_value

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
    matrices = database.import_from_database()
    mat_a = matrices['A']
    print(mat_a.mat)

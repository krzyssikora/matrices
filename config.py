DATABASE = "matrices/database/matrices_rational.sqlite"
# DATABASE = "matrices/database/matrices_rational_tmp.sqlite"
# DATABASE = "c:/Users/krzys/Documents/Python/lekcje/matrices/matrices/database/matrices_rational_tmp.sqlite"

MATRIX_NAME_RESTRICTED_WORDS = {'RREF', 'DEL', 'AUG', 'SUB', 'DET'}

help_general_intro = ['This app offers various operations on matrices with rational inputs. '
                      'It accepts both fractions and decimals.', ' ',
                      'Let M and N be the names of matrices.',
                      'The following are the available actions.',
                      'To get more details type a help command in the algebra window.',
                      '',
                      'Note that a matrix name cannot be longer than 5 characters. '
                      'It should consist of letters that may be followed by digits.']

help_general_info = [["action", "command/-s", "help command"],
                     ["clear screen", "cls", "help cls"],
                     ["multiply by a scalar", "2 * M, 1/2 * M, 1.2 * M, N = 5/2 * M", "help *"],
                     ["add matrices", "M + N", "help +"],
                     ["subtract matrices", "M - N", "help -"],
                     ["multiply matrices", "M * N", "help *"],
                     ["determinant of a matrix", "det(M)", "help det"],
                     ["inverse of a matrix", "M^(-1)", "help inv"],
                     ["transpose of a matrix", "M^T", "help T"],
                     ["augment a matrix with another", "aug(M, N)", "help aug"],
                     ["sub-matrix", "sub(M, rows, columns) - from top left or </br>"
                                    "sub(M, r0, r1, c0, c1) </br>"
                                    "- rows from r0 to r1 inclusive </br>"
                                    "- columns from c0 to c1 inclusive", "help sub"],
                     ["row echelon form", "ref(M)", "help ref"],
                     ["reduced row echelon form", "rref(M)", "help rref"],
                     ["assign result to a matrix", "M = ...</br>"
                                                   "(both to a new or existing matrix)", "help ="],
                     ["create a new matrix", "create", "help create"],
                     ["delete a matrix from memory and database </br>"
                      "or a few matrices at once", "del M, del(M) or </br>"
                                                   "del(M, N)", "help del"],
                     ]

help_commands = [['CLS', [['cls', 'Clears the screen and shows only </br>'
                                  'the matrices stored in the database.']]],
                 ['*', [['a * b', 'Multiplies two numbers that are integers (e.g. 12) </br>'
                                  'or fractions (e.g. 97/11) or decimals (e.g. 0.25)'],
                        ['a * M, M * a', 'OR multiplies a matrix M by a number a'],
                        ['M * N', 'OR multiplies matrix M by matrix N, where the number of columns </br>'
                                  'in M is the same as the number of rows in N']]],
                 ['+', [['M + N', 'Adds matrices if their dimensions (both rows and columns) are the same.']]],
                 ['-', [['M - N', 'Subtracts matrices if their dimensions (both rows and columns) are the same.']]],
                 ['DET', [['det(M)', 'Evaluates the determinant of a square matrix, i.e. a matrix</br>'
                                     'whose number of rows is equal to the number of columns.']]],
                 ['INV', [['M^(-1)', 'Finds the inverse of an invertible square matrix, i.e.</br>'
                                     'a matrix whose number of rows is equal to the number of columns and</br>'
                                     'the determinant is non-zero.']]],
                 ['T', [['M^T', 'Finds the transpose of a matrix, i.e. switches rows to columns.']]],
                 ['AUG', [['aug(M, N)', 'Augments a matrix M with N, if their numbers of rows are equal.']]],
                 ['SUB', [['sub(M, r, c)', 'Finds a sub-matrix of a given matrix with rows from 1 to r</br> '
                                           'and columns from 1 to c (inclusive).'],
                          ['sub(M, r0, r1, c0, c1)',
                           'OR finds a sub-matrix of a given matrix with rows from r0 to r1</br>'
                           'and columns from c0 to c1 (inclusive).']]],
                 ['REF', [['ref(M)', "Evaluates the row echelon form of a matrix, i.e. a form with 1's in </br>"
                                     "the leading diagonal and 0's below the diagonal."]]],
                 ['RREF', [['rref(M)', "Evaluates the reduced row echelon form of a matrix, i.e. a form with</br>"
                                       "1's in the leading diagonal and 0's both below and above the diagonal."]]],
                 ['=', [['M = ...', 'Can be used to assign result of the dotted expression to a matrix M. M can be</br>'
                                    'both a new or an existing matrix.']]],
                 ['CREATE', [['create', 'Starts the process of creating a nem matrix with either manual '
                                        'or pseudo-random inputs.'],
                             ['create(r, c)', 'Creates a new matrix with pseudo-random inputs, '
                                              'with r rows and c columns.']]],
                 ['DEL', [['del M, del(M)', 'Deletes a matrix from the memory and from the database.'],
                          ['del(M, N)', 'Deletes a few matrices from the database. Their names should be separated</br>'
                                        'by commas and they should be identical to those listed.']]],
                 ['out', [['out', 'Ends the application.']]]]

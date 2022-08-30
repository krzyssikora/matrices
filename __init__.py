from flask import Flask
# initialize global variables
# matrices_dict = dict()
# matrices_str_dict = dict()
# tmp_matrices = dict()
# matrices_names = list()
# assign_answer = [False, False, ""]

from matrices.config import _logger

app = Flask(__name__)

import matrices.views

# todo:
#  1. refreshing storage after assigning answers in user input
#  2. passing data from python to JS without hidden elements ?
#  3. 'a^-1*145/3' does not work, but 'a^-1*145*(1/3)' does
#  4. remove nonlocal variables

from flask import Flask

from matrices.config import _logger

app = Flask(__name__)

import matrices.views

# app.add_url_rule('/help', view_func=views.general_help)

# todo:
#  1. refactor read_input, now in algebra, should be in utils
#  1.1. 'a^-1*145/3' does not work, but 'a^-1*145*(1/3)' does
#  1.2. 2^3^2 does not give nice LaTeX output
#  2. add saving by click

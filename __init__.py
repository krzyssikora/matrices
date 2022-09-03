from flask import Flask

from matrices.config import _logger

app = Flask(__name__)

import matrices.views

# app.add_url_rule('/help', view_func=views.general_help)

# todo:
#  1. del(M) refreshes storage, but del(M, N) does not (because of multiple_input???)
#  3. make arrow up recall last input
#  4. 'a^-1*145/3' does not work, but 'a^-1*145*(1/3)' does
#  5. add saving by click
#  6. 2^3^2 does not give nice LaTeX output

from flask import Flask

app = Flask(__name__)

import matrices.views

# app.add_url_rule('/help', view_func=views.general_help)

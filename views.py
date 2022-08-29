from matrices import app
from matrices import matrices_dict, matrices_str_dict, tmp_matrices, matrices_names, assign_answer
from matrices import database, utils, algebra
from matrices.config import _logger
from flask import render_template, request, jsonify
import git


@app.route('/git_update', methods=['POST'])
def git_update():
    repo = git.Repo('./matrices')
    origin = repo.remotes.origin
    repo.create_head('main',
                     origin.refs.main).set_tracking_branch(origin.refs.main).checkout()
    origin.pull()
    return '', 200


@app.route('/')
def index():
    global matrices_dict, matrices_str_dict, tmp_matrices, matrices_names
    matrices_dict = database.import_from_database()
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )

#
# @app.route('/from_python')
# def send_data(js_data):
#     r = Response(response='<p>{}</p>'.format(js_data), status=200, mimetype="application/xml")
#     r.headers["Content-Type"] = "text/css; charset=utf-8"
#     return r
#

@app.route('/delete_matrix/<int:idx>', methods=['POST'])
def get_matrix_to_delete(idx):
    global matrices_dict, matrices_str_dict, tmp_matrices, matrices_names
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    _logger.debug('before remove {}'.format(len(matrices_list)))
    matrix_name_to_delete = matrices_list.pop(idx)[0]
    database.delete_matrix(matrix_name_to_delete)
    _logger.debug('after remove {}'.format(len(matrices_list)))
    matrices_dict = database.import_from_database()

    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/create_matrix/<string:matrix>', methods=['POST'])
def get_matrix_data_to_create(matrix):
    global matrices_dict, matrices_str_dict, tmp_matrices, matrices_names
    matrix = matrix.replace('minussign', '-')
    matrix = matrix.replace('slashsign', '/')
    matrix = eval(matrix)
    values = algebra.get_fractions_from_list_of_strings(matrix['values'])
    name, rows, columns = matrix['name'], matrix['rows'], matrix['columns']
    if values and name and rows and columns:
        name, rows, columns = name.upper(), int(rows), int(columns)
        new_matrix = algebra.Matrix(rows, columns, values)
        matrices_dict[name] = new_matrix
        database.save_matrix(name)
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/get_user_input')
def get_and_process_user_input():
    global matrices_dict, matrices_str_dict, tmp_matrices, matrices_names
    user_input = str(request.args.get('user_input', '')).upper()
    replacements = {
        'PLUSSIGN': '+',
        'SLASHSIGN': '/',
        'HASHSIGN': '#',
    }
    for replacement in replacements:
        user_input = user_input.replace(replacement, replacements[replacement])
    input_processed = utils.mathjax_wrap(utils.get_input_read(user_input))
    input_latexed = utils.mathjax_wrap(utils.change_to_latex(user_input))
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)

    return jsonify({
        'matrices_list': matrices_list,
        'input_processed': input_processed,
        'input_latexed': input_latexed,
    })


@app.route('/help')
def help():
    return render_template('help.html')

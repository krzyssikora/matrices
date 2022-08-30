from matrices import app
# from matrices import matrices_dict, matrices_str_dict, tmp_matrices, matrices_names, assign_answer
from matrices import database, utils, algebra
from matrices.config import _logger
from flask import render_template, request, jsonify
import git


@app.route('/git_update', methods=['POST'])
def git_update():
    if request.method == 'POST':
        repo = git.Repo('./matrices')
        origin = repo.remotes.origin
        repo.create_head('master',
                         origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
        origin.pull()
        return '', 200
    else:
        return '', 400


@app.route('/')
def index():
    matrices_dict = database.import_from_database()
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/delete_matrix/<int:idx>', methods=['POST'])
def get_matrix_to_delete(idx):
    matrices_dict = database.import_from_database()
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    matrix_name_to_delete = matrices_list.pop(idx)[0]
    database.delete_matrix(matrix_name_to_delete)

    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/create_matrix/<string:matrix>', methods=['POST'])
def get_matrix_data_to_create(matrix):
    matrices_dict = database.import_from_database()
    matrix = matrix.replace('minussign', '-')
    matrix = matrix.replace('slashsign', '/')
    matrix = eval(matrix)
    values = algebra.get_fractions_from_list_of_strings(matrix['values'])
    name, rows, columns = matrix['name'], matrix['rows'], matrix['columns']
    if values and name and rows and columns:
        name, rows, columns = name.upper(), int(rows), int(columns)
        new_matrix = algebra.Matrix(rows, columns, values)
        matrices_dict[name] = new_matrix
        database.save_matrix(name, matrices_dict)
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/get_user_input')
def get_and_process_user_input():
    matrices_dict = database.import_from_database()
    user_input = str(request.args.get('user_input', '')).upper()
    replacements = {
        'PLUSSIGN': '+',
        'SLASHSIGN': '/',
        'HASHSIGN': '#',
    }
    for replacement in replacements:
        user_input = user_input.replace(replacement, replacements[replacement])
    input_processed = utils.mathjax_wrap(utils.get_input_read(user_input, matrices_dict))
    input_latexed = utils.mathjax_wrap(utils.change_to_latex(user_input))
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    _logger.debug('user_input: {}'.format(user_input))
    _logger.debug('input_processed: {}'.format(input_processed))
    _logger.debug('input_latexed: {}'.format(input_latexed))
    return jsonify({
        'matrices_list': matrices_list,
        'input_processed': input_processed,
        'input_latexed': input_latexed,
    })


@app.route('/help')
def help():
    return render_template('help.html')

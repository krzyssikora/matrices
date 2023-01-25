from matrices import app
from matrices import database, utils, algebra, config
from flask import render_template, request, jsonify, Markup
# import git
import logging
from datetime import datetime


# @app.route('/git_update', methods=['POST'])
# def git_update():
#     if request.method == 'POST':
#         repo = git.Repo('./matrices')
#         origin = repo.remotes.origin
#         repo.create_head('master',
#                          origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
#         origin.pull()
#         return '', 200
#     else:
#         return '', 400


@app.route('/')
def index():
    matrices_dict = database.import_from_database()
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/delete_matrix/<string:matrix_name_to_delete>', methods=['POST'])
def get_matrix_to_delete(matrix_name_to_delete):
    database.delete_matrix(matrix_name_to_delete)
    matrices_dict = database.import_from_database()
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)

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
    _logger.debug(f'matrix to create. name: {name}, rows: {rows}, columns: {columns}, values: {values}')
    if values and name and rows and columns:
        name, rows, columns = name.upper(), int(rows), int(columns)
        new_matrix = algebra.Matrix(rows, columns, values)
        matrices_dict[name] = new_matrix
        database.save_matrix(name, matrices_dict)
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    _logger.debug('*' * 100)
    for mtrx in matrices_list:
        _logger.debug(f'{mtrx}')
    return render_template(
        'index.html',
        matrices_list=matrices_list
    )


@app.route('/get_user_input')
def get_and_process_user_input():
    """
    Returns:
        message_type:
        0 - clear screen
        1 - general help
        2 - command help
        3 - other input
    """
    matrices_dict = database.import_from_database()
    user_input = str(request.args.get('user_input', '')).upper().strip()

    replacements = {
        'PLUSSIGN': '+',
        'SLASHSIGN': '/',
        'HASHSIGN': '#',
    }
    for replacement in replacements:
        user_input = user_input.replace(replacement, replacements[replacement])

    if user_input == 'CLS':
        return jsonify({'message_type': 0})

    if user_input == 'HELP':
        return jsonify({'message_type': 1})

    if user_input.startswith('HELP'):
        command = user_input.split()[1]
        help_table = utils.get_matrix_help_command_menu_by_command(command)
        if help_table:
            return jsonify({
                'message_type': 2,
                'help_table': help_table,
            })
        else:
            matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
            return jsonify({
                'message_type': 3,
                'matrices_list': matrices_list,
                'input_processed': 'no such command',
                'input_latexed': user_input,
                'refresh_storage': 0,
            })

    input_processed, input_latexed, refresh_storage, saveable, output_value = \
        utils.get_input_read(user_input, matrices_dict)
    matrices_list = utils.get_list_of_matrix_dict_latexed(matrices_dict)
    return jsonify({
        'message_type': 3,
        'matrices_list': matrices_list,
        'input_processed': input_processed,
        'input_latexed': input_latexed,
        'refresh_storage': refresh_storage,
        'saveable': saveable,
        'output_value': output_value,
    })


@app.route('/get_help_command')
def get_help_command():
    help_command_id = int(request.args.get('help_command_id', ''))
    command = config.help_general_info[help_command_id + 1][-1].split()[-1]
    help_table = utils.get_matrix_help_command_menu_by_command(command)
    return jsonify({
        'help_table': help_table,
    })


@app.route('/help')
def general_help():
    help_info, table_header, table_content = utils.get_matrix_help_general_menu()
    help_content = {
        'help_info': help_info,
        'table_header': Markup(table_header),
        'table_content': [Markup(row) for row in table_content],
    }
    return render_template('help.html',
                           help_content=help_content,
                           )


# create logger in 'views'
_logger = logging.getLogger('log')
_logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
dtnow = datetime.now()
log_filename = f'{dtnow.year}-{str(dtnow.month).rjust(2, "0")}-{str(dtnow.day).rjust(2, "0")}_matrices.log'
fh = logging.FileHandler('logs/' + log_filename)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
_logger.addHandler(fh)
_logger.addHandler(ch)

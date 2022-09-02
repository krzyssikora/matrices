var matrices_names;
var algebra_chunks_list = [];
// const maxMatrixDimension = 9;
var algebra_content;

(function() {
    "use strict";
    var ajax_get = function(url, callback) {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                try {
                    var data = JSON.parse(xmlhttp.responseText);
                } catch(err) {
                    console.log(err.message + " in " + xmlhttp.responseText);
                    return;
                }
                callback(data);
            }
        };

        xmlhttp.open("GET", url, true);
        xmlhttp.send();
    };

    function convert(elt) {
        return $("<span />", { html: elt }).text();
    };

    function getHiddenData(data_id, data_type) {
        // data_id (str): element's id
        // data_type (str): either 'int' or 'object' or 'html'
        var dom_elt = document.getElementById(data_id);
        var elt_string = dom_elt.innerHTML;
        var ret_object;
        if (elt_string.length == 0) {
            ret_object = ''
        } else if (data_type == 'int') {
            ret_object = parseInt(elt_string)
        } else if (data_type == 'object') {
            elt_string = convert(elt_string);
            ret_object = JSON5.parse(elt_string);
        } else if (data_type == 'html') {
            ret_object = convert(elt_string)
        } else {
            ret_object = elt_string;
        };
        dom_elt.style.display = 'none';
        return ret_object;
    };

    function updateStorage() {
        setTimeout(() => {
            $( "#storage div.section-content" ).load(window.location.href + " #storage div.section-content>*","" );
            setTimeout(() => {
                MathJax.typesetPromise();
                ScrollToBottom(document.getElementById('storage'));
                focusOnInput();
                addListenersDeleteMatrix();
                addListenersCopyMatrixToInput();
            }, 100);
        }, 100);
    };
    // TODO the timeouts above must be changed

    function focusOnInput() {
        const input = document.getElementById('user-input');
        const end = input.value.length;
        // Move focus to end of user-input field
        input.setSelectionRange(end, end);
        input.focus();
    };

    // info that mathJax is loading
    var pop_up = document.getElementById('pop-up-universal');
    pop_up.style.display = 'block';

    var modal_content = document.getElementById('modal_div');
    var i = 0

    function checkLoaded() {
        if(window.loaded === 0) {
            for (let j=0; j<5; j++) {
                let clone = document.createElement('span');
                clone.innerHTML = 'mathematics is loading... ';
                clone.id = `wait_${i}`;
                i++;
                clone.style.color = '#' + Math.floor(Math.random()*16777215).toString(16);
                clone.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                clone.style.fontSize = (50 + Math.floor(Math.random()*35)).toString(16) + 'px';
                modal_content.appendChild(clone);
            };
            window.setTimeout(checkLoaded, 1);
        } else {
            setTimeout(() => {
                modal_content.innerHTML = '';
                pop_up.style.display = 'none';
                focusOnInput();
            }, 1)  // later change to 1000???
        };
    }
    checkLoaded();

    function sendUserInput(user_input) {
		var request = new XMLHttpRequest();
		request.open('POST', `/get_user_input/${user_input}`);
		request.send();
	};

    function ScrollToBottom(element) {
        element.scrollTop = element.scrollHeight - element.offsetHeight;
    };

    var algebra_box = document.getElementById('algebra');
    var algebra_header = document.getElementById('algebra-header');
    algebra_header.style.width = algebra_box.clientWidth;

    function createAlgebraChunk(in_text, out_text) {
        var level_0 = document.createElement('span');
        level_0.className = 'deleteicon';
        var level_1 = document.createElement('div');
        level_1.className = 'algebra-chunk';
        var level_2_cross = document.createElement('span');
        level_2_cross.innerHTML = 'x';
        var level_2_in = document.createElement('p');
        level_2_in.className = 'entered-formula';
        level_2_in.innerHTML = in_text;
        var level_2_out = document.createElement('p');
        level_2_out.className = 'app-answer';
        level_2_out.innerHTML = out_text;
        level_1.appendChild(level_2_cross);
        level_1.appendChild(level_2_in);
        level_1.appendChild(level_2_out);
        level_0.appendChild(level_1);
        level_2_cross.addEventListener('click', function(e){
            e.preventDefault();
            level_0.remove();
        })
        return level_0;
    };

    var user_input_field = document.getElementById('user-input');

    function getDataFromUserInput() {
        var initial_text = user_input_field.value;
        var replacements = {
            '+': 'plussign',
            '/': 'slashsign',
            '#': 'hashsign',
            '[': '(',
            ']': ')',
        };
        for (const [key, value] of Object.entries(replacements)) {
            initial_text = initial_text.replaceAll(key, value)
        };
        var url = '/get_user_input?user_input=' + initial_text;
        var in_text;
        var out_text;
        var refresh_storage;

        ajax_get(url, function(data) {
            if (data['message_type'] == 1) {
                window.location.href = '/help';
            } else if (data['message_type'] == 2) {
                console.log('command help')
            } else if (data['message_type'] == 3) {
                matrices_names = data['matrices_names'];
                in_text = data['input_latexed'];
                out_text = data['input_processed'];
                refresh_storage = data['refresh_storage'];
                if (refresh_storage == 1) {
                    updateStorage();
                };
                var new_element = createAlgebraChunk(in_text, out_text);
                var container = algebra_box.querySelector('.section-content');
                var last_child = document.getElementById('clearfieldicon');
                container.insertBefore(new_element, last_child);
                user_input_field.value = '';
                MathJax.typeset();
                ScrollToBottom(document.getElementById('algebra'))
                focusOnInput();
            };
        });
    };

    document.getElementById('user-input').addEventListener('keypress', (e) => {
        var key = e.charCode || e.keyCode || 0;
        if (key == 13) {
            e.preventDefault();
            getDataFromUserInput();
        }
    })

    // clicking cross in user input clears the field
    document.getElementById('user-input-clear').addEventListener('click', (e) => {
        e.preventDefault();
        user_input_field.value = '';
        focusOnInput();
    })


    function sendMatrixToDelete(idx) {
		var request = new XMLHttpRequest();
		request.open('POST', `/delete_matrix/${idx}`);
		request.send();
	};

    function sendMatrixDataToCreate(matrix) {
		var request = new XMLHttpRequest();
        var matrix_str = JSON.stringify(matrix);
		request.open('POST', `/create_matrix/${matrix_str}`);
		request.send();
	};

    var name_not_used_message = '';

    function correctMatrixName(matrix_name) {
        const hidden_matrices_names = document.getElementById('storage-names');
        hidden_matrices_names.style.display = 'block';
        matrices_names = getHiddenData('storage-names', 'object');
        hidden_matrices_names.style.display = 'none';
        if (matrices_names.includes(matrix_name)) {
            name_not_used_message = [false, `Matrix named "${matrix_name}" already exists.`]
        } else {
            name_not_used_message = [true, '']
        };

        if (!name_not_used_message[0]) {
            return name_not_used_message
        };

        for (let word of ["DET", "CLS", "HELP", "CREATE"]) {
            if (matrix_name.includes(word)) {
                return [false, `A matrix name cannot contain "${word}", it is a restricted word.`]
            };
        };

        if (matrix_name === 'T') {
            return [false, 'A matrix name cannot be "T", it is a restricted word.']
        };

        var letter_used = false;
        var digit_used = false;
        // only letters and digits allowed, digits must follow letters
        for (let letter of matrix_name) {
            if (!letter_used && ("0".charCodeAt(0) <= letter.charCodeAt(0)) && (letter.charCodeAt(0) <= "9".charCodeAt(0))) {
                return [false, "Letters must go before digits."]
            };
            if (("A".charCodeAt(0) <= letter.charCodeAt(0)) && (letter.charCodeAt(0) <= "Z".charCodeAt(0)) && digit_used) {
                return [false, "Digits must not be placed before letters."]
            };
            if (("A".charCodeAt(0) <= letter.charCodeAt(0)) && (letter.charCodeAt(0) <= "Z".charCodeAt(0))) {
                letter_used = true
            } else if (("0".charCodeAt(0) <= letter.charCodeAt(0)) && (letter.charCodeAt(0) <= "9".charCodeAt(0))) {
                digit_used = true
            } else {
                return [false, "Only letters and digits are allowed."]
            };
        };
        return [true, ''];
    };

    var rows_number;
    var columns_number;
    function correctMatrixDimension(dimension_string) {
        var dimension = parseInt(dimension_string)
        var dimension_string_2 = dimension.toString()
        if (dimension_string.length == dimension_string_2.length) {
            // maxMatrixDimension
            if ((dimension > 0) && (dimension <= 9)) {
                return [true, dimension]
            } else {
                return [false, 'dimension must be a whole number between 1 and 9']
            };
        } else {
            return [false, 'dimension must be a whole number between 1 and 9']
        };
    };

    // define divs for enetering new matrix
    var matrix_name_div = document.getElementById('matrix-name-div');
    var matrix_dimensions_div = document.getElementById('matrix-dimensions-div');
    var matrix_input_div = document.getElementById('matrix-input');
    var matrix_rest_div = document.getElementById('matrix-rest');
    var matrix_name_field;
    var rows_field;
    var columns_field;

    function refreshNewMatrixDivs() {
        matrix_name_div.innerHTML = '<label class="pop-up-form-label" for="matrix-name" id="matrix-name-label"><b>matrix name</b></label><input class="pop-up-form-input" type="text" name="matrix-name" id="matrix-name"><span class="input-error-info" id="matrix-error-info"></span>';
        matrix_name_div.style.display = 'none';
        matrix_dimensions_div.innerHTML = '<label class="pop-up-form-label" for="rows" id="rows-label"><b>number of rows</b></label><input class="pop-up-form-input" type="text" name="rows" tabindex="0" id="rows"><br><label class="pop-up-form-label" for="columns" id="columns-label"><b>number of columns</b></label><input class="pop-up-form-input" type="text" name="columns" id="columns"><span class="input-error-info" id="dimensions-error-info"></span>';
        matrix_dimensions_div.style.display = 'none';
        matrix_input_div.style.display = 'none';
        matrix_rest_div.style.display = 'none';
        matrix_name_field = document.getElementById('matrix-name');
        rows_field = document.getElementById('rows');
        columns_field = document.getElementById('columns');
    };

    refreshNewMatrixDivs();

    function makeGrid(rows_number, columns_number) {
        matrix_input_div.style.display = 'grid';
        var spot = document.getElementById('matrix-input');
        spot.innerHTML = '';
        spot.style.width = `${(30 + 6 + 6) * columns_number}px`;
        spot.style.gridTemplate = '1fr '.repeat(rows_number) + '/ ' + '1fr '.repeat(columns_number);
        var html = '';
        for (let r=0; r<rows_number; r++) {
            for (let c=0; c<columns_number; c++) {
                html += `<input type="text" class="matrix-elt" name="array" id="m_${r}_${c}"> `
            };
        };
        spot.innerHTML = html;
        document.getElementById('m_0_0').focus();
    };

    function checkDimension(field, field_str) {
        var info_dim = document.getElementById('dimensions-error-info');
        info_dim.style.display = 'none';
        var dim_checked = correctMatrixDimension(field.value);
        var dim_correct = dim_checked[0];
        var dim_message = dim_checked[1];
        if (dim_correct) {
            if (field_str == 'rows') {
                rows_number = dim_message
            } else if (field_str == 'columns') {
                columns_number = dim_message
            };
            if (rows_number > 0 && columns_number > 0) {
                matrix_dimensions_div.innerHTML = `${rows_number} rows, ${columns_number} columns <span class="input-error-info" id="dimensions-error-info"></span>`;
                matrix_rest_div.style.display = 'block';
                makeGrid(rows_number, columns_number);
            };
        } else {
            info_dim.style.display = 'block'
            info_dim.innerHTML = dim_message;
        };
    };

    function checkName(matrix_name_field) {
        var matrix_name = matrix_name_field.value.toUpperCase();
        var name_checked = correctMatrixName(matrix_name);
        var name_correct = name_checked[0];
        var name_message = name_checked[1];
        rows_number = 0;
        columns_number = 0;

        if (name_correct) {
            // show rows and columns
            matrix_dimensions_div.style.display = 'block';
            // hide matrix name
            matrix_name_div.innerHTML = `matrix name: ${matrix_name} <span class="input-error-info" id="matrix-error-info"></span>`;
            // rows_field.focus({focusVisible: true});
            rows_field.focus();
            rows_field.select();
            // get dimensions
            // rows
            // tab should focus on rows input
            rows_field.addEventListener('keydown', (e) => {
                var key = e.charCode || e.keyCode || 0;
                if ((key == 9 || key == '9') && (columns_number > 0)) {
                    e.preventDefault();
                    checkDimension(rows_field, 'rows');
                }
            });
            // enter should focus on rows input
            rows_field.addEventListener('keypress', (e) => {
                var key = e.charCode || e.keyCode || 0;
                if (key == 13) {
                    e.preventDefault();
                    checkDimension(rows_field, 'rows');
                }
            });
            // other actions should focus on rows input
            rows_field.addEventListener('change', (e) => {
                e.preventDefault();
                checkDimension(rows_field, 'rows');
            });

            // columns
            // tab should foucus on columns input
            columns_field.addEventListener('keydown', (e) => {
                var key = e.charCode || e.keyCode || 0;
                if ((key == 9 || key == '9') && (rows_number > 0)) {
                    e.preventDefault();
                    checkDimension(columns_field, 'columns');
                }
            });
            // enter should focus on columns input
            columns_field.addEventListener('keypress', (e) => {
                var key = e.charCode || e.keyCode || 0;
                if (key == 13) {
                    e.preventDefault();
                    checkDimension(columns_field, 'columns');
                }
            });
            // other actions should focus on columns input
            columns_field.addEventListener('change', (e) => {
                e.preventDefault();
                checkDimension(columns_field, 'columns');
            });
        } else {
            var info = document.getElementById('matrix-error-info');
            info.style.display = 'block';
            info.innerHTML = name_message;
        };
    };

    document.getElementById('add-matrix').addEventListener('click', (e) => {
        e.preventDefault();
        refreshNewMatrixDivs();
        document.getElementById('enter_matrix').style.display = 'block';
        matrix_name_div.style.display = 'block';
        matrix_dimensions_div.style.display = 'none';
        matrix_input_div.style.display = 'none';
        matrix_rest_div.style.display = 'none';

        document.getElementById('matrix-name').focus();

        // check name
        // tab should foucus on rows input
        matrix_name_field.addEventListener('keydown', (e) => {
            var key = e.charCode || e.keyCode || 0;
            if (key == 9 || key == '9') {
                e.preventDefault();
                checkName(matrix_name_field);
            }
        });
        // enter should focus on rows input
        matrix_name_field.addEventListener('keypress', (e) => {
            var key = e.charCode || e.keyCode || 0;
            if (key == 13) {
                e.preventDefault();
                checkName(matrix_name_field);
            }
        });
        // other actions should focus on rows input
        matrix_name_field.addEventListener('change', (e) => {
            e.preventDefault();
            checkName(matrix_name_field);
        });
    });


    document.getElementById('new-matrix-confirm-button').addEventListener('click', e => {
        e.preventDefault();
        document.getElementById('enter_matrix').style.display = 'none';
        var name = matrix_name_field.value;
        var rows = rows_field.value;
        var columns = columns_field.value;
        var node_values = document.getElementsByName('array');
        var values = [];
        for (var i=0; i<node_values.length; i++) {
            values.push(node_values[i].value.replaceAll('-', 'minussign').replaceAll('/', 'slashsign') || 0);
        ;}

        var matrix = {'name': name, 'rows': rows, 'columns': columns, 'values': values};
        algebra_content = $("#algebra div.section-content").html();
        sendMatrixDataToCreate(matrix);
        updateStorage();
        
        addListenersDeleteMatrix();
        addListenersCopyMatrixToInput();
    });
    
    addListenersDeleteMatrix();
    addListenersCopyMatrixToInput();

    function addListenersDeleteMatrix () {
        $('[id*="storage-cross"]').click((e) => {
            e.preventDefault();
            let el = e.currentTarget
            let idx = el.id.match(/.+-(\d+)$/)[1]
            let dom_idx = `storage-matrix-${idx}`;
            document.getElementById(dom_idx).remove();
            // window.location.href = '/';
            sendMatrixToDelete(idx);
        })
    };

    function addListenersCopyMatrixToInput () {
        $("#storage p.app-answer").click(e => {
            e.preventDefault();
            let el = e.currentTarget
            var m_name = el.dataset.name;
            const input = document.getElementById('user-input');
            input.value = input.value + m_name;
            const end = input.value.length;
            // Move focus to end of user-input field
            input.setSelectionRange(end, end);
            input.focus();
        })
    };

})();

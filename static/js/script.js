var matrices_names;
// const maxMatrixDimension = 9;
var algebra_content;
var algebra_content_idx = 1;
var previousInputs = [];
var previousInputIndex = -1;
var output_value;
var pop_up = document.getElementById('pop-up-universal');
var modal_content = document.getElementById('modal_div');

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
        window.loaded = 1;
    };

    function convert(elt) {
        return $("<span />", { html: elt }).text();
    };

    function updateStorage() {
        window.loaded = 0;
        checkLoaded();
        updateStorage1(updateStorage2);
        setTimeout( function(){
            ScrollToBottom(document.getElementById('storage'));
            focusOnInput();
            addStorageListeners();
          }, 500 );
    };

    function updateStorage1(callback) {
        $( "#storage div.section-content" ).load(window.location.href + " #storage div.section-content>*","" );
        setTimeout( function(){
            callback();
          }, 500 );
    };
    function updateStorage2() {
        MathJax.typeset();
        updateStorage3();
    };

    function updateStorage3() {
        window.loaded = 1;
    };

    function focusOnInput() {
        const input = document.getElementById('user-input');
        const end = input.value.length;
        // Move focus to end of user-input field
        input.setSelectionRange(end, end);
        input.focus();
    };

    function showMathsLoadingPopUp() {
        pop_up.style.display = 'block';
        var i = 0
        for (let j=0; j<20; j++) {
            let clone = document.createElement('span');
            clone.innerHTML = 'mathematics is loading... ';
            clone.id = `wait_${i}`;
            i++;
            clone.style.color = '#' + Math.floor(Math.random()*16777215).toString(16);
            clone.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            clone.style.fontSize = (50 + Math.floor(Math.random()*35)).toString(16) + 'px';
            modal_content.appendChild(clone);
        };
    };

    function hideMathsLoadingPopUp() {
        modal_content.innerHTML = '';
        pop_up.style.display = 'none';
        ScrollToBottom(document.getElementById('storage'));
        focusOnInput();
    };

    function checkLoaded() {
        // info that mathJax is loading on start
        showMathsLoadingPopUp();
        if(window.loaded === 0) {
            window.setTimeout(checkLoaded, 5);
        } else {
            hideMathsLoadingPopUp();
        };
    }
    checkLoaded();

    function ScrollToBottom(element) {
        element.scrollTop = element.scrollHeight - element.offsetHeight + 100;
    };

    var algebra_box = document.getElementById('algebra');
    var algebra_header = document.getElementById('algebra-header');
    algebra_header.style.width = algebra_box.clientWidth;

    function createAlgebraChunk(in_text, out_text, saveable, output_value) {
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
        if (saveable) {
            var level_2_save = document.createElement('span');
            level_2_save.innerHTML = '&darr;'
            level_2_save.id = `get_new_matrix_name-${algebra_content_idx}`;
            level_1.appendChild(level_2_save);
            
        };
        level_1.appendChild(level_2_in);
        level_1.appendChild(level_2_out);
        level_0.appendChild(level_1);
        level_2_cross.addEventListener('click', function(e){
            e.preventDefault();
            level_0.remove();
        });
        return level_0;
    };

    var user_input_field = document.getElementById('user-input');

    function getDataFromUserInput(callback) {
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
            if (data['message_type'] == 0) {
                // clear screen
                const algebra_elements = algebra_box.querySelectorAll('.deleteicon');
                algebra_elements.forEach(element => {
                    element.remove()
                });
                algebra_content_idx = 1;
                user_input_field.value = '';
            } else if (data['message_type'] == 1) {
                // general help
                window.location.href = '/help';
            } else if (data['message_type'] == 2) {
                // command help
                var help_table = data['help_table'];
                user_input_field.value = '';
                $.getScript('/static/js/script_help.js', function(){
                	showHelpCommandInfo(help_table);
                });
            } else if (data['message_type'] == 3) {
                // other (algebraic)
                in_text = data['input_latexed'];
                out_text = data['input_processed'];
                refresh_storage = data['refresh_storage'];
                if (refresh_storage == 1) {
                    updateStorage();
                };
                var saveable = data['saveable'];
                var output_value = data['output_value'];
                var new_element = createAlgebraChunk(in_text, out_text, saveable, output_value);
                var container = algebra_box.querySelector('.section-content');
                var last_child = document.getElementById('clearfieldicon');
                container.insertBefore(new_element, last_child);
                user_input_field.value = '';
                if (saveable) {
                    addListenerNewMatrixName(output_value);
                };
                algebra_content_idx ++;
                MathJax.typeset();
                ScrollToBottom(document.getElementById('algebra'))
                focusOnInput();
            };
            callback();
        });

        
    };

    user_input_field.addEventListener('keypress', (e) => {
        var key = e.charCode || e.keyCode || 0;
        if (key == 13) {
            // ENTER pressed
            e.preventDefault();
            previousInputs.push(user_input_field.value);
            previousInputIndex = previousInputs.length - 1;
            showMathsLoadingPopUp();
            getDataFromUserInput(hideMathsLoadingPopUp);
        };
    });

    user_input_field.addEventListener('keydown', (e) => {
        var key = e.charCode || e.keyCode || 0;
        if (key == 38) {
            // ARROW UP pressed
            e.preventDefault();
            user_input_field.value = previousInputs[previousInputIndex];
            previousInputIndex --;
            if (previousInputIndex < 0) {
                previousInputIndex = previousInputs.length - 1
            };
            const end = user_input_field.value.length;
            // Move focus to end of user-input field
            user_input_field.setSelectionRange(end, end);
            user_input_field.focus();
        } else if (key == 40) {
            // ARROW DOWN pressed
            e.preventDefault();
            user_input_field.value = previousInputs[previousInputIndex];
            previousInputIndex ++;
            if (previousInputIndex >= previousInputs.length) {
                previousInputIndex = 0
            };
            const end = user_input_field.value.length;
            // Move focus to end of user-input field
            user_input_field.setSelectionRange(end, end);
            user_input_field.focus();
        };
    });

    // clicking cross in user input clears the field
    document.getElementById('user-input-clear').addEventListener('click', (e) => {
        e.preventDefault();
        user_input_field.value = '';
        focusOnInput();
    })


    function sendMatrixToDelete(matrix_name) {
		var request = new XMLHttpRequest();
		request.open('POST', `/delete_matrix/${matrix_name}`);
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
        matrices_names = [];
        for (let elt of document.querySelectorAll('[data-name]')) {
            matrices_names.push(elt.dataset.name)
        };
        if (matrices_names.includes(matrix_name)) {
            name_not_used_message = [false, `Matrix named "${matrix_name}" already exists.`]
        } else {
            name_not_used_message = [true, '']
        };

        if (!name_not_used_message[0]) {
            return name_not_used_message
        };

        for (let word of ["DET", "CLS", "HELP", "CREATE", "DEL"]) {
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
    // define divs for new matrix name from output
    var matrix_only_name_div = document.getElementById('matrix-only-name-div');
    var matrix_name_rest_div = document.getElementById('matrix-name-rest');
    var matrix_only_name_field;
    

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
            // tab should focus on columns input
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
        setTimeout(() => {
            updateStorage();
            addStorageListeners();
        }, 500);
    });

    function checkNameAndConfirm(matrix_only_name_field, output_value) {
        var matrix_name = matrix_only_name_field.value.toUpperCase();
        var name_checked = correctMatrixName(matrix_name);
        var name_correct = name_checked[0];
        var name_message = name_checked[1];

        if (name_correct) {
            document.getElementById('new_matrix_name').style.display = 'none';
            var name = matrix_only_name_field.value;
            var rows = output_value['rows'];
            var columns = output_value['columns'];
            var values = output_value['values'];
            var matrix = {'name': name, 'rows': rows, 'columns': columns, 'values': values};
            sendMatrixDataToCreate(matrix);
            setTimeout(() => {
                updateStorage();
                addStorageListeners();
            }, 500);
        } else {
            var info = document.getElementById('matrix-name-error-info');
            info.style.display = 'block';
            info.innerHTML = name_message;
        };
    };
    
    addStorageListeners();

    function addListenersDeleteMatrix () {
        $('[id*="storage-cross"]').click((e) => {
            e.preventDefault();
            let el = e.currentTarget
            let idx = el.id.match(/.+-(\d+)$/)[1]
            let dom_idx = `storage-matrix-${idx}`;
            let matrix_name = document.getElementById(dom_idx).children[1].dataset.name
            document.getElementById(dom_idx).remove();
            // window.location.href = '/';
            sendMatrixToDelete(matrix_name);
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

    function addListenerAddMatrix() {
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
    };

    function addListenerNewMatrixName(output_value) {
        document.getElementById(`get_new_matrix_name-${algebra_content_idx}`).addEventListener('click', function(e) {
            e.preventDefault();
            matrix_only_name_div.innerHTML = '<label class="pop-up-form-label" for="matrix-only-name" id="matrix-only-name-label"><b>enter matrix name for storing the output</b></label><input class="pop-up-form-input" type="text" name="matrix-only-name" id="matrix-only-name"><span class="input-error-info" id="matrix-name-error-info"></span>';
            matrix_only_name_div.style.display = 'none';
            matrix_name_rest_div.style.display = 'none';
            matrix_only_name_field = document.getElementById('matrix-only-name');
            document.getElementById('new_matrix_name').style.display = 'block';
            matrix_only_name_div.style.display = 'block';
            matrix_name_rest_div.style.display = 'block';

            matrix_only_name_field.focus();
   
            // enter 
            matrix_only_name_field.addEventListener('keypress', (e) => {
                var key = e.charCode || e.keyCode || 0;
                if (key == 13) {
                    e.preventDefault();
                    checkNameAndConfirm(matrix_only_name_field, output_value);
                }
            });
            // confirm button
            document.getElementById('new-matrix-name-confirm-button').addEventListener('click', e => {
                e.preventDefault();
                checkNameAndConfirm(matrix_only_name_field, output_value) 
            });
        })
    }

    function addStorageListeners() {
        addListenersCopyMatrixToInput();
        addListenerAddMatrix();
        addListenersDeleteMatrix();
    };

})();

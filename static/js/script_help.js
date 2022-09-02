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

    var showHelpCommandInfo = function(helpTable) {
        document.getElementById('help-command').style.display = 'block';
        var domHelpTable = document.getElementById('help-command-table');
        domHelpTable.innerHTML = helpTable;
        domHelpTable.addEventListener('click', function() {
            document.getElementById('help-command').style.display = 'none';
        })
    };

    $('[id*="help-row"]').click((e) => {
        e.preventDefault();
        let el = e.currentTarget
        let idx = el.id.match(/.+-(\d+)$/)[1]
        var url = '/get_help_command?help_command_id=' + idx;

        ajax_get(url, function(data) {
            let helpTable = data['help_table'];
            showHelpCommandInfo(helpTable);
            // MathJax.typeset();
        });
    });

})();

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

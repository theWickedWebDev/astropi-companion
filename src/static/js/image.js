function image(path, selector, args) {
    var img = document.createElement("IMG");
    img.src = path
    $(selector).html(
        $('<img>', {
            id: 'solved',
            src: path,
            width: '100%',
            ...args
        })
    )
}
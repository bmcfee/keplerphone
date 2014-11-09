// nothing here yet

function update_kois(data) {
    $.each(data, function(koi) {
        $('#koi').append($('<option>', {value : data[koi].id}).text(data[koi].name));
    });
}

function update_scales(data) {
    $.each(data, function(s) {
        $('#scale').append($('<option>', {value : data[s]}).text(data[s]));
    });
}

function play() {
    var source = $('input[name=source]:checked').val();
    var kic = $('#koi').val();
    var scale = $('#scale').val();

    if (source == 'free') {
        kic = $('#koi-free').val();
    }

    $('#plot').attr('src', '/img/' + kic);

    MIDIjs.play('/keplerphone/' + kic + '/' + scale);

}



$(document).ready(function() {

    $.ajax({url: '/ids', dataType: 'json'}).done(update_kois);
    $.ajax({url: '/scales', dataType: 'json'}).done(update_scales);

    $('#playfree').click(play);

    $('#stop').click(function() { MIDIjs.stop(); });
});

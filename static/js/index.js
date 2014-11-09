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

function play_music() {
    var kic = $('#koi').val();

    var scale = $('#scale').val();

    var url = '/keplerphone/' + kic + '/' + scale;

    MIDIjs.play(url);
}

$(document).ready(function() {

    $.ajax({url: '/ids', dataType: 'json'}).done(update_kois);
    $.ajax({url: '/scales', dataType: 'json'}).done(update_scales);
});

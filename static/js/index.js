// nothing here yet

function update_kois(data) {
    $.each(data, function(koi) {
        $('#koi').append($('<option>', {value : data[koi].id}).text(data[koi].name));
    });
    update_share();
}

function update_scales(data) {
    $.each(data, function(s) {
        $('#scale').append($('<option>', {value : data[s]}).text(data[s]));
    });

    var prekic = $('#prescale').val()
    if (prescale != "None") {
        $('#scale').val(prekic);
    }
    update_share();
}

function update_img() {
    var kic = get_kic();

    $('#plot').attr('src', '/img/' + kic);

}

function play() {
    MIDIjs.stop();
    var scale = $('#scale').val();
    var speed = $('#speed').val();
    var kic = get_kic();

    update_img();

    $('#prekic').val(kic);
    $('#prescale').val(scale);

    update_share(kic);

    MIDIjs.play('/keplerphone/' + kic + '/' + encodeURIComponent(scale) + '/' + speed);
}

function get_kic() {

    var source = $('input[name=source]:checked').val();
    var kic = $('#koi').val();

    if (source == 'free') {
        kic = $('#koi-free').val();
    }

    return kic;
}


function update_control() {
    update_share();
    MIDIjs.stop();
}


$(document).ready(function() {

    $.ajax({url: '/scales', dataType: 'json'}).done(update_scales);

    var prekic = $('#prekic').val()
    if (prekic != "None") {
        $('#koi-free').val(prekic);
        $('#koi-free-radio').prop('checked', true);
        update_img();
        update_share(prekic);
    }

    $('#playfree').click(play);

    $('#stop').click(update_control);
    $('#scale').change(update_control);
    $('#speed').change(update_control);

    $('#koi').change(function() {
        $('#koi-fixed').prop('checked', true);
        var kic = get_kic();
        $('#plot').attr('src', '/img/' + kic);
        update_share();
        MIDIjs.stop();
    });

    $.ajax({url: '/ids', dataType: 'json'}).done(update_kois);

});

function get_url() {

    var url = window.location.origin + '/' + get_kic() + '/' + $('#prescale').val() + '/' + $('#speed').val();
    
    return url;
}

function update_download() {
    var scale = $('#scale').val();
    var speed = $('#speed').val();
    var kic = get_kic();

    var href = '/keplerphone/' + kic + '/' + encodeURIComponent(scale) + '/' + speed;

    $('#download').attr('href', href);
}

function update_share() {

    var kic = get_kic();

    var text = 'Listening to KIC' + kic + ' on The KeplerPhone';
    var url = get_url();

    var href = 'http://twitter.com/intent/tweet?text=' + encodeURIComponent(text)
             + '&hashtags=keplerphone'
             + '&url=' + encodeURIComponent(url) ;

    $('#share').attr('href', href);

    window.history.pushState(null, $('title').text(), url);
    update_download();
}

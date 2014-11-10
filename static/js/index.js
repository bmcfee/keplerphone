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
    var kic = $('#koi').val();

    $('#plot').attr('src', '/img/' + kic);

}

function play() {
    MIDIjs.stop();
    var source = $('input[name=source]:checked').val();
    var kic = $('#koi').val();
    var scale = $('#scale').val();
    var speed = $('#speed').val();

    if (source == 'free') {
        kic = $('#koi-free').val();
    }

    update_img();

    $('#prekic').val(kic);
    $('#prescale').val(scale);

    update_share('Listening to KIC' + kic + ' on The KeplerPhone');

    MIDIjs.play('/keplerphone/' + kic + '/' + encodeURIComponent(scale) + '/' + speed);
}



$(document).ready(function() {

    $.ajax({url: '/scales', dataType: 'json'}).done(update_scales);

    var prekic = $('#prekic').val()
    if (prekic != "None") {
        $('#koi-free').val(prekic);
        $('#koi-free-radio').prop('checked', true);
        $('#plot').attr('src', '/img/' + prekic);
        update_share('Listening to KIC' + prekic + ' on The KeplerPhone');
    }

    $('#playfree').click(play);

    $('#stop').click(function() { MIDIjs.stop(); });

    $('#koi').change(function() {
        var kic = $('#koi').val();
        $('#koi-fixed').prop('checked', true);
        $('#plot').attr('src', '/img/' + kic);
        MIDIjs.stop();
    });

    $.ajax({url: '/ids', dataType: 'json'}).done(update_kois);

});

function get_url() {

    var url = window.location.origin + '/' +  $('#prekic').val() + '/' + $('#prescale').val() + '/' + $('#speed').val();
    
    return url;
}

function update_download() {
    var kic = $('#koi').val();
    var scale = $('#scale').val();
    var speed = $('#speed').val();
    var source = $('input[name=source]:checked').val();

    if (source == 'free') {
        kic = $('#koi-free').val();
    }

    var href = '/keplerphone/' + kic + '/' + encodeURIComponent(scale) + '/' + speed;

    console.log(scale);

    $('#download').attr('href', href);
}

function update_share(text) {

    var url = get_url();

    var href = 'http://twitter.com/intent/tweet?text=' + encodeURIComponent(text)
             + '&hashtags=keplerphone'
             + '&url=' + encodeURIComponent(url) ;

    $('#share').attr('href', href);

    $('#linkurl').val(url);
    update_download();
}

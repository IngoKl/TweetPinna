var root = location.protocol + '//' + location.host;
var glob_loaded = 0;
var glob_more = 100;
var glob_last_dic = 0;

function load_tweets(loaded, more, clear) {
    $('#load-more').html('Loading ...')
    $.getJSON(root + '/ajax/get/hashtags', {
        f: loaded,
        t: loaded + more
    }, function(data) {
        glob_loaded = loaded + more;

        if (clear == 1) {
            $("#hashtags").html('');
        }

        if (Object.keys(data).length > 0) {

            sorted = Object.keys(data).sort(function(a, b) {
                return data[b] - data[a]
            });
            for (var i = 0; i < sorted.length; i++) {
                $("#hashtags").append('<span class="hashtag">#' + sorted[i] + ' <span class="hashtag-count">' + data[sorted[i]] + '</span></span>');
            }

            $('#load-more').html('Load More');
            $('#load-more').show();

            if (Object.keys(data).length < more) {
                console.log(Object.keys(data).length)
                $('#load-more').hide();
            }
        } else {
            $('#load-more').hide();
        }

    });
}


$(document).ready(function() {
    //Welcome
    var refresh_time = 30000 //0.5 Minute;
    if ($("#dic").length) {
        setInterval(function() {
            $.getJSON(root + '/ajax/get/docs-in-collection', function(data) {
                $('#dic').html(data[1]);
                $('#led').html(data[0]);
                if (glob_last_dic > 0) {
                    est_tweets_per_hour = (data[1] - glob_last_dic) * 120
                    $('#tph').html(est_tweets_per_hour);
                }

                glob_last_dic = data[1];
                console.log(glob_last_dic);
            });
        }, refresh_time);
    }

    // Hashtags
    if ($("#hashtag-number").length) {
        $('#load-more').hide();
        load_tweets(0, glob_more, 1);

        $.getJSON(root + '/ajax/get/hashtags-number', function(data) {
            $('#hashtag-number').html(data);
        });


        $('#load-more').bind('click', function() {
            load_tweets(glob_loaded, glob_more)
            return false;
        });
    }

    // Media
    if ($("#storage-size").length) {
        $.getJSON(root + '/ajax/get/storage-size', function(data) {
            $('#storage-size').html(data + ' MB');
        });
    }


    //Statistics
    if ($("#statistics").length) {
        $.getJSON(root + '/ajax/get/statistics', function(data) {
            $('#statistics').html('<ul class="statistics-list" id="statistics_list">');
            jQuery.each(data, function(key, value) {
                $('#statistics_list').append('<li>' + value[0] + ': <i>' + value[1] + '</i></li>');
            });
        });
    }
});
jQuery(document).ready(function() {

    jQuery('select.wym_select_pagelink').each( function() {
        jQuery(this).attr('disabled', true).html('<option>Please wait, loading pages...</option>');
        var selected_val = jQuery(this).val();
        jQuery.ajax ({
            type: "POST",
            url: "/pages/pagelinks/",
            data: ({lang: language}),
            dataType: "html",
            cache: false, //VITAL line: the getJON func does not prevent caching!
            success: function (html) {//Call this func when we have some data
                    jQuery('.wym_select_pagelink').empty().html(html).attr('disabled', false);
                    jQuery('.wym_select_pagelink option:first').attr('selected', 'selected');
            }
        });
        jQuery('select.wym_select_pagelink').attr('selected', 'selected');       
    });

});

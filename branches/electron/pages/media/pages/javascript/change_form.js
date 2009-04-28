$(function() {
    // Hide form rows containing only hidden inputs
    $('.form-row').each(function() {
        if (!$('p, label, select, input:not([type=hidden])', this).length) {
            $(this).hide();
        }
    });
    
    // Focus the title
    $('#id_title').focus();
    
    // Automatically update the slug when typing the title
    var slug_auto = true;
    var slug = $("#id_slug").change(function() {
        slug_auto && (slug_auto = false);
    });
    $("#id_title").keyup(function() {
        slug_auto && slug.val(URLify(this.value, 64));
    });
    
    // Translation helper
    $('#translation-helper-select').change(function() {
        var index = this.selectedIndex;
        if (index) {
            var array = window.location.href.split('?');
            $.get(array[0]+'traduction/'+this.options[index].value+'/', function(html) {
                $('#translation-helper-content').html(html).show();
            });
        } else {
            $('#translation-helper-content').hide();
        }
    });
    
    // Select the appropriate template option
    var template = $.query.get('template');
    if (template) {
        $('#id_template option').each(function() {
            if (template == this.value) {
                $(this).attr('selected', true);
                return false;
            }
        });
    }
    
    // Confirm language and template change if page is not saved
    $.each(['language', 'template'], function(i, label) {
        var select = $('#id_'+label);
        if (select.length) {
            select.change(function() {
                var href = window.location.href.split('?');
                var query = $.query.set(label, select.val()).toString();
                window.location.href = href[0]+query;
            });
        }
    });
    
    // Disable the page content if the page is a redirection
    var redirect = $('#id_redirect_to').change(update_redirect);
    var affected = $('.form-row:has(#id_language), .form-row:has(#id_template), .module-content .form-row')
        .each(function () {
            var element = $(this).css('position', 'relative');
            $('<div class="overlay"></div>').css({
                'position': 'absolute',
                'display': 'none',
                'opacity': '0',
                'top': '0',
                'left': '0',
                'height': element.height(),
                'width': element.width()
            }).appendTo(element);
        });
    function update_redirect() {
        if (redirect.val()) {
            affected.css('opacity', '0.5').find('.overlay').show();
        } else {
            affected.css('opacity', '1').find('.overlay').hide();
        }
    }
    update_redirect();
    
    // Content revision selector
    $('.revisions').change(function () {
        var select = $(this);
        var val = select.val();
        if (val) {
            $.get(val, function (html) {
                var formrow = select.parents('.form-row');
                if ($('a.disable', formrow).length) {
                    $('iframe', formrow)[0].contentWindow.document.getElementsByTagName("body")[0].innerHTML = html;
                } else {
                    var formrow_textarea = $('textarea', formrow).val(html);
                    // support for WYMeditor
                    if (WYMeditor) {
                        $(WYMeditor.INSTANCES).each(function (i, wym) {
                            if (formrow_textarea.attr('id') === wym._element.attr('id')) {
                                wym.html(html);
                            }
                        });
                    }
                }
            });
        }
        return false;
    });
});

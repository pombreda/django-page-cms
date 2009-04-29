/* Initialization of the change_list page - this script is run once everything is ready. */

$(function() {
    var submenu_cache = [];
    
    function save_expanded() {
        var col = [];
        $('a.expanded').each(function() {
            col.push(this.id.substring(1));
        });
        // expire in 12 days
        pages.cookie('tree_expanded', col.join(','), {'expires':12});
    }
    
    function remove_children(id) {
        $('.child-of-'+id).each(function() {
            remove_children(this.id.substring(9));
            $(this).remove();
        });
    }
    
    function get_children(id, list) {
        $('.child-of-'+id).each(function() {
            list.push(this);
            get_children(this.id.substring(9), list);
            return list
        });
    }
    
    var selected_page = false;
    var action = false;
    
    // let's start event delegation
    $('#changelist').click(function(e) {
        // I want a link to check the class
        if(e.target.tagName == 'IMG' || e.target.tagName == 'SPAN')
            var target = e.target.parentNode;
        else
            var target = e.target;
        var jtarget = $(target);
        
        if(jtarget.hasClass('move')) {
            var page_id = e.target.id.split('move-link-')[1];
            selected_page = page_id;
            action = 'move';
            $('#changelist table').removeClass('table-selected');
            $('tr').removeClass('selected').removeClass('target');
            $('#page-row-'+page_id).addClass('selected');
            var children = [];
            get_children(page_id, children);
            for(var i=0; i < children.length; i++) {
                $(children[i]).addClass('selected');
            }
            $('#changelist table').addClass('table-selected');
            return false;
        }
        
        if(jtarget.hasClass('addlink')) {
            $('tr').removeClass('target');
            $('#changelist table').removeClass('table-selected');
            var page_id = target.id.split('add-link-')[1];
            selected_page = page_id;
            action = 'add';
            $('tr').removeClass('selected');
            $('#page-row-'+page_id).addClass('selected');
            $('.move-target-container').hide();
            $('#move-target-'+page_id).show();
            return false;
        }
        
        if(jtarget.hasClass('move-target')) {
            if(jtarget.hasClass('left'))
                var position = 'left';
            if(jtarget.hasClass('right'))
                var position = 'right';
            if(jtarget.hasClass('first-child'))
                var position = 'first-child';
            var target_id = target.parentNode.id.split('move-target-')[1];
            if(action=='move') {
                var msg = $('<span>Please wait...</span>');
                $($('#page-row-'+selected_page+' td')[0]).append(msg);
                $.post(selected_page+'/move-page/', {
                        position:position,
                        target:target_id
                    },
                    function(html) {
                        $('#changelist').html(html);
                        var msg = $('<span>Successfully moved</span>');
                        var message_target = '#page-row-'+selected_page
                        if(!$(message_target).length)
                            message_target = '#page-row-'+target_id
                        $(message_target).addClass('selected');
                        $($(message_target+' td')[0]).append(msg);
                        msg.fadeOut(5000);
                    }
                );
                $('.move-target-container').hide();
            }
            if(action=='add') {
                var query = $.query.set('target', target_id).set('position', position).toString();
                window.location.href += 'add/'+query;
            }
            return false;
        }
        
        if(jtarget.hasClass('expand-collapse')) {
            var the_id = jtarget.attr('id').substring(1);
            jtarget.toggleClass('expanded');
            if(jtarget.hasClass('expanded')) {
                if (submenu_cache[the_id]){
                    $('#page-row-'+the_id).after(submenu_cache[the_id]);
                } else {
                    $.get(the_id+'/sub-menu/',
                        function(html) {
                            $('#page-row-'+the_id).after(html);
                            submenu_cache[the_id] = html;
                            /* TODO: recursively re-expand submenus according to cookie */
                        }
                    );
                }
            } else {
                remove_children(the_id);
            }
            save_expanded();
            return false;
        };
        
        return true;
    });
    
    // Set the publication status
    $('#changelist').change(function(e) {
        var select = $(e.target);
        if (select.is('select.publish-select')) {
            var url = select.attr('name').split('status-')[1]+'/';
            var img = select.parent().find('img');
            pages.update_published_icon(url, select, img);
        }
    });
});

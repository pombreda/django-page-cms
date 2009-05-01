/* Initialization of the change_list page - this script is run once everything is ready. */

$(function () {
    var action = false;
    var selected_page = false;
    var submenu_cache = [];
    
    // Get an array of the TR elements that are children of the given page id
    // The list argument should not be used (it is only used by the recursion)
    function get_children(id, list) {
        list = list || [];
        $('.child-of-'+id).each(function() {
            list.push(this);
            get_children(this.id.substring(9), list);
        });
        return list;
    }
    
    // Request and insert to the table the children of the given page id
    function add_children(id) {
        submenu_cache[id] ? add() : $.get(id+'/sub-menu/', add);
        
        function add(html) {
            html && (submenu_cache[id] = html); // If a new request was made, save the HTML to the cache
            $('#page-row-'+id).after(submenu_cache[id]);
            var expanded = get_expanded();
            $('.child-of-'+id).each(function() {
                var i = this.id.substring(9);
                if ($.inArray(i, expanded) != -1) {
                    $('#c'+i).addClass('expanded');
                    add_children(i);
                }
            });
        }
    }
    
    // Remove the children of the given page id from the table
    function rem_children(id) {
        $('.child-of-'+id).each(function () {
            rem_children(this.id.substring(9));
            $(this).remove();
        });
    }
    
    // Add a page id to the list of expanded pages
    function add_expanded(id) {
        var expanded = get_expanded();
        if ($.inArray(id, expanded) == -1) {
            expanded.push(id);
            set_expanded(expanded);
        }
    }
    
    // Remove a page id from the list of expanded pages
    function rem_expanded(id) {
        var expanded = get_expanded();
        var index = $.inArray(id, expanded);
        if (index != -1) {
            // The following code is based on J. Resig's optimized array remove
            var rest = expanded.slice(index+1);
            expanded.length = index;
            expanded.push.apply(expanded, rest);
            set_expanded(expanded);
        }
    }
    
    // Get the list of expanded page ids from the cookie
    function get_expanded() {
        var cookie = pages.cookie('tree_expanded');
        return cookie ? cookie.split(',') : [];
    }
    
    // Save the list of expanded page ids to the cookie
    function set_expanded(array) {
        pages.cookie('tree_expanded', array.join(','), { 'expires': 14 }); // expires after 12 days
    }
    
    // let's start event delegation
    $('#changelist').click(function (e) {
        var link = $(e.target).parents('a').andSelf().filter('a');
        if (link.length) {
            // Toggles a previous action to come back to the initial state
            if (link.hasClass('selected')) {
                selected_page = action = '';
                link.removeClass('selected');
                $('#changelist tr').removeClass('highlighted insertable');
                return false;
                
            // Ask where to move the page to
            } else if (link.hasClass('movelink')) {
                action = 'move';
                $('#changelist a').removeClass('selected');
                selected_page = link.addClass('selected').attr('id').split('move-link-')[1];
                $('#changelist tr').removeClass('highlighted insertable');
                $('#page-row-'+selected_page).add(get_children(selected_page)).addClass('highlighted');
                $('#changelist tr:not(.highlighted)').addClass('insertable');
                return false;
                
            // Ask where to insert the new page
            } else if (link.hasClass('addlink')) {
                action = 'add';
                selected_page = link.addClass('selected').attr('id').split('add-link-')[1];
                $('#changelist tr').removeClass('highlighted insertable');
                $('#page-row-'+selected_page).addClass('highlighted insertable');
                return false;
                
            // Move or add the page and come back to the initial state
            } else if (link.hasClass('move-target')) {
                var position = link.attr('class').match(/left|right|first-child/)[0];
                var id = link.parent().attr('id').split('move-target-')[1];
                
                $('#changelist a').removeClass('selected');
                $('#changelist tr').removeClass('insertable');
                $('#page-row-'+selected_page+' th').append('<img src="/media/pages/images/waiting.gif" alt="Loading" />');
                
                if (action == 'move') {
                    $.post(selected_page+'/move-page/', { position: position, target: id },
                        function (html) {
                            $('#changelist').html(html);
                            pages.fade_color($('#page-row-'+selected_page).add(get_children(selected_page)));
                        }
                    );
                } else if (action == 'add') {
                    window.location.href += 'add/'+$.query.set('target', id).set('position', position).toString();
                }
                return false;
                
            // Expand or collapse pages
            } else if (link.hasClass('expand-collapse')) {
                var id = link.attr('id').substring(1);
                if (link.toggleClass('expanded').hasClass('expanded')) {
                    add_expanded(id);
                    add_children(id);
                } else {
                    rem_expanded(id);
                    rem_children(id);
                }
                return false;
            }
        }
    });
    
    // Set the publication status
    $('#changelist').change(function (e) {
        var select = $(e.target);
        if (select.is('select.publish-select')) {
            var url = select.attr('name').split('status-')[1]+'/';
            var img = select.parent().find('img');
            pages.update_published_icon(url, select, img);
        }
    });
});

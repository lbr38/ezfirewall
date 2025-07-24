/**
 *  Event: print a copy icon on element with .copy class
 */
$(document).on('mouseenter','.copy',function () {
    // If the element is a <pre> tag, the copy icon is in the top right corner
    if ($(this).is('pre')) {
        $(this).append('<img src="/assets/icons/duplicate.svg" class="icon-lowopacity icon-copy-top-right margin-left-5" title="Copy to clipboard">');
    } else {
        $(this).append('<img src="/assets/icons/duplicate.svg" class="icon-lowopacity icon-copy margin-left-5" title="Copy to clipboard">');
    }
});

/**
 *  Event: remove copy icon on element with .copy class
 */
$(document).on('mouseleave','.copy',function () {
    $(this).find('.icon-copy').remove();
    $(this).find('.icon-copy-top-right').remove();
});

/**
 *  Event: copy parent text on click on element with .icon-copy class
 */
$(document).on('click','.icon-copy, .icon-copy-top-right',function (e) {
    // Prevent parent to be triggered
    e.stopPropagation();

    var text = $(this).parent().text().trim();

    navigator.clipboard.writeText(text).then(() => {
        printAlert('Copied to clipboard', 'success');
    },() => {
        printAlert('Failed to copy', 'error');
    });
});

/**
 *  Event: copy on click on element with .copy-input-onclick class
 */
$(document).on('click','.copy-input-onclick',function (e) {
    var text = $(this).val().trim();

    navigator.clipboard.writeText(text).then(() => {
        printAlert('Copied to clipboard', 'success');
    },() => {
        printAlert('Failed to copy', 'error');
    });
});

/**
 *  Event: click on a reloadable table page number
 */
$(document).on('click','.reloadable-table-page-btn',function () {
    /**
     *  Get table name and offset from parent
     */
    var table = $(this).parents('.reloadable-table').attr('table');
    var page = $(this).attr('page');

    /**
     *  Calculate offset (page * 10 - 10)
     */
    offset = parseInt(page) * 10 - 10;

    /**
     *  If offset is negative, set it to 0
     */
    if (offset < 0) {
        offset = 0;
    }

    /**
     *  Set cookie for PHP to load the right content
     *  e.g tables/tasks/list-done/offset
     */
    mycookie.set('tables/' + table + '/offset', offset, 1);

    reloadTable(table, offset);
});

/**
 * Ajax: Get and reload container
 * @param {*} container
 */
function reloadContainer(container)
{
    return new Promise((resolve, reject) => {
        try {
            /**
             *  If the container to reload does not exist, return
             */
            if (!$('.reloadable-container[container="' + container + '"]').length) {
                return;
            }

            /**
             *  Check if container has children with class .veil-on-reload
             *  If so print a veil on them
             */
            printLoadingVeilByParentClass('reloadable-container[container="' + container + '"]');

            ajaxRequest(
                // Controller:
                'general',
                // Action:
                'getContainer',
                // Data:
                {
                    sourceUrl: window.location.href,
                    sourceUri: window.location.pathname,
                    container: container
                },
                // Print success alert:
                false,
                // Print error alert:
                true,
                // Reload container:
                [],
                // Execute functions on success:
                [
                    // Replace container with itself, with new content
                    "$('.reloadable-container[container=\"" + container + "\"]').replaceWith(jsonValue.message)",
                    // Reload opened or closed elements that were opened/closed before reloading
                    "reloadOpenedClosedElements()"
                ]
            ).then(() => {
                // Hide loading icon
                hideLoading();

                // Resolve promise
                resolve('Container reloaded');
            });
        } catch (error) {
            // Reject promise
            reject('Failed to reload container');
        }
    });
}

/**
 * Ajax: Get and reload table
 * @param {*} table
 * @param {*} offset
 */
function reloadTable(table, offset = 0)
{
    ajaxRequest(
        // Controller:
        'general',
        // Action:
        'getTable',
        // Data:
        {
            table: table,
            offset: offset,
            sourceUrl: window.location.href,
            sourceUri: window.location.pathname,
            sourceGetParameters: getGetParams()
        },
        // Print success alert:
        false,
        // Print error alert:
        true,
        // Reload container:
        [],
        // Execute functions on success:
        [
            // Replace table with itself, with new content
            "$('.reloadable-table[table=\"" + table + "\"]').replaceWith(jsonValue.message)"
        ]
    );
}

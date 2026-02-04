/**
 * Event: when the date selection is changed
 */
$(document).on('change','input#top-10-drop-day',function() {
    // Get selected value
    const date = $(this).val();

    // Add a get parameter
    appendGetParam('date', date);

    // Destroy and recreate chart with new days value
    EChart.recreate('barHorizontal', 'top-source-ip-chart', true, 120000);
    EChart.recreate('barHorizontal', 'top-destination-ports-chart', true, 120000);
});

/**
 * Event: when the period (days) selection is changed
 */
$(document).on('change','select#drop-count-by-day-period',function() {
    // Get selected value
    const days = $(this).val();

    // Destroy and recreate chart with new days value
    EChart.recreate('line', 'drop-count-by-day-chart', true, 120000, days);
});

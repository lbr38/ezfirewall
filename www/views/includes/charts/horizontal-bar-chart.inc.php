<canvas id="<?= $chartId ?>"></canvas>

<script>
$(document).ready(function() {
    // Remove loading spinner
    $('#<?= $chartId ?>-loading').remove();

    // Data
    var barChartData = {
        datasets: [{
            data: [<?= implode(',', $datas) ?>],
            // backgroundColor: [<?= implode(',', $backgrounds) ?>],
            borderWidth: 0.4,
            maxBarThickness: 20,
        }],
        labels: [<?= implode(',', $labels) ?>],
    };

    // Options
    var barChartOptions = {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: "<?= $title ?>",
                color: '#8A99AA',
                font: {
                    size: 14
                },
            }
        },
        elements: {
            point: {
                radius: 0
            },
            bar: {
                borderWidth: 2,
            }
        },
        scales: {
            x: {
                ticks: {
                    color: '#8A99AA',
                    font: {
                        size: 14,
                        family: 'Roboto'
                    },
                    stepSize: 1
                }
            },
            y: {
                ticks: {
                    color: '#8A99AA',
                    font: {
                        size: 12,
                        family: 'Roboto'
                    },
                    stepSize: 1
                }
            }
        }
    }

    // Print chart
    var ctx = document.getElementById('<?= $chartId ?>').getContext("2d");
    window.myBar = new Chart(ctx, {
        type: "bar",
        data: barChartData,
        options: barChartOptions
    });
});
</script>
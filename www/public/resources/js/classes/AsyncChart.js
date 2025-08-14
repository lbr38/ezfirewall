/**
 *  Create charts with ChartJS
 *  - A <canvas> element with the same ID as the chart must exist in the HTML
 *  - The server must return the data with all the data needed to create the chart (.vars.inc.php file must exist)
 *  - (optional) A loading spinner with the ID <chartID>-loading must exist in the HTML
 */
class AsyncChart
{
    /**
     * Get chart data by ID
     * @param {*} id
     * @returns
     */
    get(id)
    {
        return new Promise((resolve, reject) => {
            try {
                ajaxRequest(
                    // Controller:
                    'chart',
                    // Action:
                    'get',
                    // Data:
                    {
                        id: id,
                        sourceGetParameters: getGetParams()
                    },
                    // Print success alert:
                    false,
                    // Print error alert:
                    true
                ).then(() => {
                    // Parse the response and store it in the class properties
                    self.title       = jsonValue.message.title;
                    self.data        = jsonValue.message.data;
                    self.labels      = jsonValue.message.labels;
                    self.backgrounds = jsonValue.message.backgrounds;

                    // For debugging purposes only
                    // console.log("title: " + self.title);
                    // console.log("data: " + JSON.stringify(self.data));
                    // console.log("labels: " + JSON.stringify(self.labels));
                    // console.log("backgrounds: " + JSON.stringify(self.backgrounds));

                    // Resolve promise
                    resolve('Chart data retrieved');
                });
            } catch (error) {
                // Reject promise
                reject('Failed to get chart data');
            }
        });
    }

    /**
     * Create a bar chart from the given ID
     * @param {*} id
     * @returns
     */
    bar(id)
    {
        // Get chart data
        this.get(id).then(() => {
            // Remove loading spinner
            $('#' + id + '-loading').remove();

            // Data
            var barChartData = {
                datasets: [{
                    data: self.data,
                    backgroundColor: self.backgrounds,
                    borderWidth: 0.4,
                    maxBarThickness: 20,
                }],
                labels: self.labels,
            };

            // Options
            var barChartOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: self.title,
                    }
                },
                elements: {
                    point: {
                        radius: 0
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
            var ctx = document.getElementById(id).getContext("2d");
            window.myBar = new Chart(ctx, {
                type: "bar",
                data: barChartData,
                options: barChartOptions
            });
        });
    }

    /**
     * Create a horizontal bar chart from the given ID
     * @param {*} id
     * @returns
     */
    horizontalBar(id)
    {
        // Get chart data
        this.get(id).then(() => {
            // Remove loading spinner
            $('#' + id + '-loading').remove();

            // Data
            var barChartData = {
                datasets: [{
                    data: self.data,
                    backgroundColor: self.backgrounds,
                    borderWidth: 0.4,
                    maxBarThickness: 20,
                }],
                labels: self.labels,
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
                        text: self.title,
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
            var ctx = document.getElementById(id).getContext("2d");
            window.myBar = new Chart(ctx, {
                type: "bar",
                data: barChartData,
                options: barChartOptions
            });
        });
    }

    /**
     * Create a pie chart from the given ID
     * @param {*} id
     * @returns
     */
    pie(id)
    {
        // Get chart data
        this.get(id).then(() => {
            // Remove loading spinner
            $('#' + id + '-loading').remove();

            // Data
            var pieChartData = {
                datasets: [{
                    data: self.data,
                    backgroundColor: self.backgrounds,
                    borderWidth: 0.4,
                    maxBarThickness: 20,
                }],
                labels: self.labels,
            };

            // Options
            var pieChartOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            font: {
                                size: 14,
                                family: 'Roboto',
                            },
                            color: '#8A99AA',
                            usePointStyle: true
                        },
                        display: true,
                        position: 'left'
                    },
                },
            }

            // Print chart
            var ctx = document.getElementById(id).getContext("2d");
            window.myPie = new Chart(ctx, {
                type: "pie",
                data: pieChartData,
                options: pieChartOptions
            });
        });
    }
}

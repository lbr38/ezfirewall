<section class="main-container reloadable-container height-100" container="port">
    <h3 class="margin-top-10">PORT <?= $port ?></h3>

    <div class="div-generic-blue">
        <h6 class="margin-top-0 margin-bottom-20">TOP 10 BLOCKED IP ON PORT <?= $port ?></h6>

        <div class="grid grid-rfr-1-2 column-gap-40 row-gap-40">
            <div>
                <p><code><?= $port ?>/TCP</code></p>

                <div class="echart-container">
                    <div id="top-blocked-ips-tcp-chart-loading" class="echart-loading">
                        <img src="/assets/icons/loading.svg" class="icon-np" />
                    </div>

                    <div id="top-blocked-ips-tcp-chart" class="echart min-height-300"></div>
                </div>
            </div>

            <div>
                <p><code><?= $port ?>/UDP</code></p>

                <div class="echart-container">
                    <div id="top-blocked-ips-udp-chart-loading" class="echart-loading">
                        <img src="/assets/icons/loading.svg" class="icon-np" />
                    </div>

                    <div id="top-blocked-ips-udp-chart" class="echart min-height-300"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="div-generic-blue">
        <h6 class="margin-top-0">DROP COUNT BY DAY</h6>

        <div class="echart-container">
            <div id="drop-count-by-day-port-chart-loading" class="echart-loading">
                <img src="/assets/icons/loading.svg" class="icon-np" />
            </div>

            <div id="drop-count-by-day-port-chart" class="echart min-height-500"></div>
        </div>
    </div>

    <div class="div-generic-blue">
        <?php
        \Controllers\Layout\Table\Render::render('port/blocked-ips'); ?>
    </div>

    <script>
        $(document).ready(function () {
            new EChart('nightingale', 'top-blocked-ips-tcp-chart', true, 120000);
            new EChart('nightingale', 'top-blocked-ips-udp-chart', true, 120000);
            new EChart('line', 'drop-count-by-day-port-chart', false, 120000);
        });
    </script>
</section>

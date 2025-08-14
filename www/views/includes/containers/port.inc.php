<section class="main-container reloadable-container height-100" container="port">
    <h3 class="margin-top-10">PORT <?= $port ?></h3>

    <div class="div-generic-blue">
        <h6 class="margin-top-0 margin-bottom-20">TOP 10 BLOCKED IP ON PORT <?= $port ?></h6>

        <div class="grid grid-rfr-1-2 column-gap-15">
            <div>
                <p><span class="label-black"><?= $port ?>/TCP</span></p>

                <div class="relative">
                    <div id="top-blocked-ips-tcp-chart-loading" class="loading-veil">
                        <img src="/assets/icons/loading.svg" class="icon-np">
                    </div>

                    <canvas id="top-blocked-ips-tcp-chart"></canvas>
                </div>
            </div>

            <div>
                <p><span class="label-black"><?= $port ?>/UDP</span></p>

                <div class="relative">
                    <div id="top-blocked-ips-udp-chart-loading" class="loading-veil">
                        <img src="/assets/icons/loading.svg" class="icon-np">
                    </div>

                    <canvas id="top-blocked-ips-udp-chart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <div class="div-generic-blue">
        <?php
        \Controllers\Layout\Table\Render::render('port/blocked-ips'); ?>
    </div>

    <script>
        $(document).ready(function () {
            mychart.pie('top-blocked-ips-tcp-chart');
            mychart.pie('top-blocked-ips-udp-chart');
        });
    </script>
</section>

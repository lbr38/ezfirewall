<section class="main-container reloadable-container height-100" container="ip">
    <h3 class="margin-top-10">IP <?= $ip ?></h3>

    <div class="div-generic-blue">
        <div class="grid grid-rfr-1-2 column-gap-40 row-gap-40">
            <div>
                <h6 class="margin-top-0 margin-bottom-20">TOP 10 BLOCKED PORTS FOR <?= $ip ?></h6>

                <div class="echart-container">
                    <div id="top-blocked-ports-chart-loading" class="echart-loading">
                        <img src="/assets/icons/loading.svg" class="icon-np" />
                    </div>

                    <div id="top-blocked-ports-chart" class="echart min-height-300"></div>
                </div>
            </div>

            <div>
                <?php
                \Controllers\Layout\Table\Render::render('ip/blocked-ports'); ?>
            </div>
        </div>
    </div>

    <div class="div-generic-blue">
        <h6 class="margin-top-0">DROP COUNT BY DAY</h6>

        <div class="echart-container">
            <div id="drop-count-by-day-ip-chart-loading" class="echart-loading">
                <img src="/assets/icons/loading.svg" class="icon-np" />
            </div>

            <div id="drop-count-by-day-ip-chart" class="echart min-height-400"></div>
        </div>
    </div>

    <div class="div-generic-blue grid grid-rfr-1-2 column-gap-15 row-gap-40">
        <div>
            <h6 class="margin-top-0 margin-bottom-20">IP LOCATION</h6>

            <div class="ip-location grid grid-2 column-gap-15 row-gap-15" ip="<?= $ip ?>">            
                <p>Country</p>
                <div class="flex align-item-center column-gap-10">
                    <p class="ip-location-country">Loading...</p>
                    <p class="ip-location-flag"></p>
                </div>

                <p>Country Code</p>
                <p class="ip-location-country-code">Loading...</p>

                <p>Region</p>
                <p class="ip-location-region">Loading...</p>

                <p>City</p>
                <p class="ip-location-city">Loading...</p>

                <p>ISP</p>
                <p class="ip-location-isp">Loading...</p>
            </div>
        </div>

        <div>
            <?php
            \Controllers\Layout\Table\Render::render('ip/dropped-date'); ?>
        </div>
    </div>

    <script>
        $(document).ready(function () {
            new EChart('nightingale', 'top-blocked-ports-chart', true, 120000);
            new EChart('line', 'drop-count-by-day-ip-chart', false, 120000);
            myiplocate.locateReplace('.ip-location');
        });
    </script>
</section>

<section class="main-container reloadable-container height-100" container="ip">
    <h3><?= $ip ?></h3>

    <div class="div-generic-blue">
        <div class="grid grid-2 column-gap-15">
            <div>
                <h5>Top 10 blocked ports for this IP</h5>
                <?php
                if (empty($topBlockedPorts)) {
                    echo '<p class="note">Nothing for now!</p>';
                } ?>

                <div>
                    <?php
                    $chartId = 'top-blocked-ports-chart';
                    $datas = [];
                    $labels = [];
                    $backgrounds = [];

                    foreach ($topBlockedPorts as $myIp) {
                        $labels[] = '"' . $myIp['Dest_port'] . '"';
                        $datas[] = '"' . $myIp['Count'] . '"';
                        $backgrounds[] = '"#ffffff"';
                    }

                    include(ROOT . '/views/includes/charts/pie-chart.inc.php');

                    unset($chartId, $labels, $datas, $backgrounds, $topBlockedPorts, $myIp); ?>
                </div>
            </div>

            <div>
                <?php
                \Controllers\Layout\Table\Render::render('ip/blocked-ports'); ?>
            </div>
        </div>
    </div>

    <div class="div-generic-blue grid grid-2 column-gap-15">
        <div>
            <h5>Location</h5>

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
    </div>

    <script>
        $(document).ready(function () {
            myIpLocate.locateReplace('.ip-location');
        });
    </script>
</section>

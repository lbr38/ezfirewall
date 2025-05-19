<section class="main-container reloadable-container height-100" container="charts">
    <div class="div-generic-blue">
        <p>Most blocked IP is <span class="label-black"><?= $mostBlockedIP['Source_ip'] ?></span> (blocked <?= $mostBlockedIP['count'] ?> times since <?= $firstDate ?>)</p>
        <br>
        <p>Most blocked port is <span class="label-black"><?= $mostBlockedPort['port'] ?></span> (blocked <?= $mostBlockedPort['count'] ?> times since <?= $firstDate ?>)</p>
    </div>

    <div class="div-generic-blue height-100">
        <form method="get">
            <div class="flex align-item-center column-gap-10">
                <input type="date" class="input-medium" name="date" value="<?= $date ?>" min="<?= $firstDate ?>" max="<?= $lastDate ?>">
                <button type="submit" class="btn-small-green">Select</button>
            </div>
        </form>

        <div id="main-charts" class="grid grid-2 column-gap-40">
            <div>
                <?php
                $chartId = 'top-source-ip-chart';
                $title = 'Top 10 IP addresses blocked on ' . strtolower($dateTitle);
                $datas = [];
                $labels = [];
                $backgrounds = [];

                foreach ($topBlockedIPs as $ip) {
                    $labels[] = '"' . $ip['Source_ip'] . '"';
                    $datas[] = '"' . $ip['Count'] . '"';
                    $backgrounds[] = '"#ffffff"';
                }

                include(ROOT . '/views/includes/charts/horizontal-bar-chart.inc.php');

                unset($labels, $datas, $backgrounds); ?>
            </div>

            <div>
                <?php
                $chartId = 'top-destination-ports-chart';
                $title = 'Top 10 destination ports blocked on ' . strtolower($dateTitle);
                $datas = [];
                $labels = [];
                $backgrounds = [];

                foreach ($topDestinationPorts as $port) {
                    $labels[] = '"Port ' . $port['Dest_port'] . '"';
                    $datas[] = '"' . $port['Count'] . '"';
                    $backgrounds[] = '"#ffffff"';
                }

                include(ROOT . '/views/includes/charts/horizontal-bar-chart.inc.php');
                
                unset($labels, $datas, $backgrounds); ?>
            </div>
        </div>
    </div>
</section>

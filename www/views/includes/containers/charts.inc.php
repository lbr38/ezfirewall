<section class="main-container reloadable-container margin-top-10 height-100" container="charts">
    <div class="div-generic-blue">
        <div class="flex column-gap-10">
            <img src="/assets/icons/info.svg" class="icon-np mediumopacity-cst">
            <p>Most blocked IP is <a href="/ip?ip=<?= $mostBlockedIP['Source_ip'] ?>" target="_blank" rel="noopener"><span class="label-black"><?= $mostBlockedIP['Source_ip'] ?></span></a> (blocked <?= $mostBlockedIP['count'] ?> times since <?= $firstDate ?>)</p>
        </div>
        
        <div class="flex column-gap-10 margin-top-10">
            <img src="/assets/icons/info.svg" class="icon-np mediumopacity-cst">
            <p>Most blocked port is <a href="/port?port=<?= $mostBlockedPort['port'] ?>" target="_blank" rel="noopener"><span class="label-black"><?= $mostBlockedPort['port'] ?> (<?= $mostBlockedPort['protocol'] ?>)</span></a> (blocked <?= $mostBlockedPort['count'] ?> times since <?= $firstDate ?>)</p>
        </div>
    </div>

    <div class="div-generic-blue height-100">
        <form method="get">
            <div class="flex align-item-center column-gap-10">
                <input type="date" class="input-medium" name="date" value="<?= $date ?>" min="<?= $firstDate ?>" max="<?= date('Y-m-d') ?>">
                <button type="submit" class="btn-small-green">Select</button>
            </div>
        </form>

        <div id="main-charts" class="grid grid-2 column-gap-40">
            <div class="relative">
                <div id="top-source-ip-chart-loading" class="loading-veil">
                    <img src="/assets/icons/loading.svg" class="icon-np">
                </div>

                <canvas id="top-source-ip-chart"></canvas>
            </div>

            <div class="relative">
                <div id="top-destination-ports-chart-loading" class="loading-veil">
                    <img src="/assets/icons/loading.svg" class="icon-np">
                </div>

                <canvas id="top-destination-ports-chart"></canvas>
            </div>
        </div>
    </div>

    <div class="grid grid-rfr-1-2 column-gap-15 div-generic-blue">
        <?php
        \Controllers\Layout\Table\Render::render('charts/blocked-ips'); ?>
    </div>

    <script>
        $(document).ready(function() {
            mychart.horizontalBar('top-source-ip-chart');
            mychart.horizontalBar('top-destination-ports-chart');
        });
    </script>
</section>

<section class="main-container reloadable-container margin-top-10 height-100" container="charts">
    <div class="div-generic-blue">
        <div class="flex column-gap-10">
            <img src="/assets/icons/info.svg" class="icon-np mediumopacity-cst">
            <p>Most dropped IP is <a href="/ip?ip=<?= $mostBlockedIP['Source_ip'] ?>" target="_blank" rel="noopener"><code><?= $mostBlockedIP['Source_ip'] ?></code></a> (blocked <?= $mostBlockedIP['count'] ?> times since <?= $firstDate ?>)</p>
        </div>
        
        <div class="flex column-gap-10 margin-top-10">
            <img src="/assets/icons/info.svg" class="icon-np mediumopacity-cst">
            <p>Most dropped port is <a href="/port?port=<?= $mostBlockedPort['port'] ?>" target="_blank" rel="noopener"><code><?= $mostBlockedPort['port'] ?>/<?= $mostBlockedPort['protocol'] ?></code></a> (blocked <?= $mostBlockedPort['count'] ?> times since <?= $firstDate ?>)</p>
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
        \Controllers\Layout\Table\Render::render('home/dropped-ips-count');
        \Controllers\Layout\Table\Render::render('home/dropped-ips-date'); ?>
    </div>

    <script>
        $(document).ready(function() {
            new AsyncChart('horizontalBar', 'top-source-ip-chart', true, 120000);
            new AsyncChart('horizontalBar', 'top-destination-ports-chart', true, 120000);
        });
    </script>
</section>

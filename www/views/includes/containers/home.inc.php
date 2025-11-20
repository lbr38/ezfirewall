<section class="main-container reloadable-container margin-top-10" container="charts">
    <div class="flex column-gap-50 row-gap-20 flex-wrap align-items-center div-generic-blue">
        <div>
            <h6 class="margin-top-0">MOST DROPPED IP</h6>
            <p title="blocked <?= $mostBlockedIP['count'] ?> times since <?= $firstDate ?>"><a href="/ip?ip=<?= $mostBlockedIP['Source_ip'] ?>" target="_blank" rel="noopener"><code><?= $mostBlockedIP['Source_ip'] ?></code></a></p>
        </div>
        
        <div>
            <h6 class="margin-top-0">MOST DROPPED PORT</h6>
            <p title="blocked <?= $mostBlockedPort['count'] ?> times since <?= $firstDate ?>"><a href="/port?port=<?= $mostBlockedPort['port'] ?>" target="_blank" rel="noopener"><code><?= $mostBlockedPort['port'] ?>/<?= $mostBlockedPort['protocol'] ?></code></a></p>
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

    <div class="div-generic-blue">
        <h6 class="margin-top-0">DROP COUNT BY DAY</h6>

        <div class="relative">
            <div id="drop-count-by-day-chart-loading" class="loading-veil">
                <img src="/assets/icons/loading.svg" class="icon-np">
            </div>

            <canvas id="drop-count-by-day-chart" class="min-height-400"></canvas>
        </div>
    </div>

    <div class="grid grid-rfr-1-2 column-gap-50 row-gap-40 div-generic-blue">
        <?php
        \Controllers\Layout\Table\Render::render('home/dropped-ips-count');
        \Controllers\Layout\Table\Render::render('home/dropped-ips-date'); ?>
    </div>

    <script>
        $(document).ready(function() {
            new AsyncChart('horizontalBar', 'top-source-ip-chart', true, 120000);
            new AsyncChart('horizontalBar', 'top-destination-ports-chart', true, 120000);
            new AsyncChart('line', 'drop-count-by-day-chart', false, 120000);
        });
    </script>
</section>

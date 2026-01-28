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
        <div class="flex flex-wrap justify-space-between column-gap-10 row-gap-10">
            <h6 class="margin-top-0">TOP 10 DROPPED IP & PORTS</h6>

            <input id="top-10-drop-day" type="date" class="input-medium" name="date" value="<?= $date ?>" min="<?= $firstDate ?>" max="<?= date('Y-m-d') ?>">
        </div>

        <div id="main-charts">
            <div class="echart-container">
                <div id="top-source-ip-chart-loading" class="echart-loading">
                    <img src="/assets/icons/loading.svg" class="icon-np" />
                </div>

                <div id="top-source-ip-chart" class="echart min-height-500"></div>
            </div>

            <div class="echart-container">
                <div id="top-destination-ports-chart-loading" class="echart-loading">
                    <img src="/assets/icons/loading.svg" class="icon-np" />
                </div>

                <div id="top-destination-ports-chart" class="echart min-height-500"></div>
            </div>
        </div>
    </div>

    <div class="div-generic-blue">
        <div class="flex flex-wrap justify-space-between column-gap-10 row-gap-10">
            <h6 class="margin-top-0">DROP COUNT BY DAY</h6>

            <select id="drop-count-by-day-period" class="select-medium margin-bottom-10">
                <option value="1">1 day</option>
                <option value="7" selected>7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">365 days</option>
            </select>
        </div>

        <div class="echart-container">
            <div id="drop-count-by-day-chart-loading" class="echart-loading">
                <img src="/assets/icons/loading.svg" class="icon-np" />
            </div>

            <div id="drop-count-by-day-chart" class="echart min-height-400"></div>
        </div>
    </div>

    <div class="grid grid-rfr-1-2 column-gap-50 row-gap-40 div-generic-blue">
        <?php
        \Controllers\Layout\Table\Render::render('home/dropped-ips-count');
        \Controllers\Layout\Table\Render::render('home/dropped-ips-date'); ?>
    </div>

    <script>
        $(document).ready(function() {
            new EChart('barHorizontal', 'top-source-ip-chart', true, 120000);
            new EChart('barHorizontal', 'top-destination-ports-chart', true, 120000);
            new EChart('line', 'drop-count-by-day-chart', true, 120000, 7);
        });
    </script>
</section>

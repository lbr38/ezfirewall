<div class="reloadable-table" table="<?= $table ?>" offset="<?= $reloadableTableOffset ?>">
    <h5>All blocked IPs (<?= $reloadableTableTotalItems ?>)</h5>

    <?php
    if (empty($reloadableTableContent)) {
        echo '<p class="note">Nothing for now!</p>';
    }

    if (!empty($reloadableTableContent)) : ?>
        <div class="grid grid-3 column-gap-15 margin-top-15 margin-bottom-10">
            <p><b>IP</b></p>
            <p><b>Count</b></p>
            <p><b>Location</b></p>
        </div>

        <?php
        foreach ($reloadableTableContent as $item) : ?>
            <div class="table-container grid-3 bck-blue-alt">
                <p><a href="/ip?ip=<?= $item['Source_ip'] ?>"><b><?= $item['Source_ip'] ?></b></a></p>
                <p><?= $item['Count'] ?></p>
                <div class="ip-location" ip="<?= $item['Source_ip'] ?>">
                    <p class="ip-location-flag">
                        <img src="/assets/icons/loading.svg" class="icon-np" />
                    </p>
                </div>
            </div>
            <?php
        endforeach ?>
        
        <div class="flex justify-end margin-top-10">
            <?php \Controllers\Layout\Table\Render::paginationBtn($reloadableTableCurrentPage, $reloadableTableTotalPages); ?>
        </div>
        <?php
    endif ?>

    <script>
        $(document).ready(function () {
            myIpLocate.locateReplace('.ip-location');
        });
    </script>
</div>

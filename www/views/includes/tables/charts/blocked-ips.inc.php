<div class="reloadable-table" table="<?= $table ?>" offset="<?= $reloadableTableOffset ?>">
    <h6 class="margin-top-0 margin-bottom-20">ALL BLOCKED IPs (<?= $reloadableTableTotalItems ?>)</h6>

    <?php
    if (empty($reloadableTableContent)) {
        echo '<p class="note">Nothing for now!</p>';
    }

    if (!empty($reloadableTableContent)) : ?>
        <div class="grid grid-2 column-gap-15 margin-top-15 margin-bottom-10">
            <p><b>IP</b></p>
            <p><b>Count</b></p>
        </div>

        <?php
        foreach ($reloadableTableContent as $item) : ?>
            <div class="table-container grid-2 wordbreakall bck-blue-alt">
                <div class="flex align-center column-gap-10">
                    <p><a href="/ip?ip=<?= $item['Source_ip'] ?>" target="_blank" rel="noopener"><b><?= $item['Source_ip'] ?></b></a></p>
                    <div class="ip-location" ip="<?= $item['Source_ip'] ?>">
                        <p class="ip-location-flag">
                            <img src="/assets/icons/loading.svg" class="icon-np" />
                        </p>
                    </div>
                </div>
                <p><?= $item['Count'] ?></p>
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
            myiplocate.locateReplace('.ip-location');
        });
    </script>
</div>

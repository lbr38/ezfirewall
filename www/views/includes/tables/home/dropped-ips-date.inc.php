<div class="reloadable-table" table="<?= $table ?>" offset="<?= $reloadableTableOffset ?>">
    <h6 class="margin-top-0 margin-bottom-20">DROPPED IPs BY DATE (<?= $reloadableTableTotalItems ?>)</h6>

    <?php
    if (empty($reloadableTableContent)) {
        echo '<p class="note">Nothing for now!</p>';
    }

    if (!empty($reloadableTableContent)) : ?>
        <div class="grid grid-3 column-gap-15 margin-top-15 margin-bottom-10">
            <p><b>Date</b></p>
            <p><b>Dropped IP & port</b></p>
            <p><b>Inbound interface</b></p>
        </div>

        <?php
        foreach ($reloadableTableContent as $item) : ?>
            <div class="table-container grid-3 wordbreakall bck-blue-alt">
                <div class="flex flex-direction-column row-gap-5">
                    <p><?= $item['Date'] ?></p>
                    <p class="mediumopacity-cst"><?= $item['Time'] ?></p>
                </div>

                <div class="flex flex-direction-column row-gap-5">
                    <div class="flex align-center column-gap-10">
                        <p><a href="/ip?ip=<?= $item['Source_ip'] ?>" target="_blank" rel="noopener"><?= $item['Source_ip'] ?></a></p>
                        <div class="ip-location" ip="<?= $item['Source_ip'] ?>">
                            <p class="ip-location-flag">
                                <img src="/assets/icons/loading.svg" class="icon-np" />
                            </p>
                        </div>
                    </div>
            
                    <p><a href="/port?port=<?= $item['Dest_port'] ?>" target="_blank" rel="noopener"><code><?= $item['Dest_port'] . '/' . $item['Protocol'] ?></code></a></p>
                </div>

                <p><code><?= $item['Interface_inbound'] ?></code></p>

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

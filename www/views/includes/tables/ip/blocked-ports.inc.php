<div class="reloadable-table" table="<?= $table ?>" offset="<?= $reloadableTableOffset ?>">
    <h6 class="margin-top-0 margin-bottom-20">ALL BLOCKED PORTS (<?= $reloadableTableTotalItems ?>)</h6>

    <?php
    if (empty($reloadableTableContent)) {
        echo '<p class="note">Nothing for now!</p>';
    }

    if (!empty($reloadableTableContent)) : ?>
        <div class="grid grid-2 column-gap-15 margin-top-15 margin-bottom-10">
            <p><b>Port</b></p>
            <p><b>Count</b></p>
        </div>

        <?php
        foreach ($reloadableTableContent as $item) : ?>
            <div class="table-container grid-2 bck-blue-alt">
                <div class="flex align-item-center column-gap-10">
                    <p><a href="/port?port=<?= $item['Dest_port'] ?>" target="_blank" rel="noopener"><?= $item['Dest_port'] ?></a></p>
                    <code><?= $item['Protocol'] ?></code>
                </div>
                <p class="font-size-14"><?= $item['Count'] ?></p>
            </div>
            <?php
        endforeach ?>
        
        <div class="flex justify-end margin-top-10">
            <?php \Controllers\Layout\Table\Render::paginationBtn($reloadableTableCurrentPage, $reloadableTableTotalPages); ?>
        </div>
        <?php
    endif ?>
</div>

<div class="reloadable-table" table="<?= $table ?>" offset="<?= $reloadableTableOffset ?>">
    <h5>All blocked ports (<?= $reloadableTableTotalItems ?>)</h5>

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
                <p><?= $item['Dest_port'] ?></p>
                <p><?= $item['Count'] ?></p>
            </div>
            <?php
        endforeach ?>
        
        <div class="flex justify-end margin-top-10">
            <?php \Controllers\Layout\Table\Render::paginationBtn($reloadableTableCurrentPage, $reloadableTableTotalPages); ?>
        </div>
        <?php
    endif ?>
</div>

<footer class="margin-bottom-40">
    <div class="text-center margin-auto">
        <p class="lowopacity-cst">Ezfirewall - release version <?= VERSION ?></p>
        <br>
        <p class="lowopacity-cst">Ezfirewall is a free and open source software, licensed under the <a target="_blank" rel="noopener noreferrer" href="https://www.gnu.org/licenses/gpl-3.0.en.html">GPLv3</a> license.</p>
        <br><br><br>
    </div>
</footer>

<script src="/resources/js/general.js?<?= VERSION ?>"></script>
<script src="/resources/js/functions.js?<?= VERSION ?>"></script>

<!-- Import some classes -->
<script src="/resources/js/classes/Layout.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/Container.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/Table.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/Cookie.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/IpLocate.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/Alert.js?<?= VERSION ?>"></script>
<script src="/resources/js/classes/AsyncChart.js?<?= VERSION ?>"></script>

<script>
    const mylayout = new Layout();
    const mycontainer = new Container();
    const mytable = new Table();
    const mycookie = new Cookie();
    const myiplocate = new IpLocate();
    const myalert = new Alert();
    const mychart = new AsyncChart();
</script>


<?php
if (!empty($jsFiles)) {
    foreach ($jsFiles as $jsFile) {
        if (is_file(ROOT . '/public/resources/js/' . $jsFile . '.js')) {
            echo '<script src="/resources/js/' . $jsFile . '.js?' . VERSION . '"></script>';
        }
    }
} ?>
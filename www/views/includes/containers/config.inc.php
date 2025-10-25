<section class="main-container reloadable-container" container="config">
    <div class="div-generic-blue flex flex-wrap align-item-center column-gap-50 row-gap-15">
        <p class="mediumopacity-cst">IPv4 inbound default policy: <span class="bold"><?php echo $ipv4DefaultInputPolicy ?? 'N/A'; ?></span></p>
        <p class="mediumopacity-cst">Log dropped IPv4 traffic: <span class="bold"><?php echo isset($ipv4LogdroppedTraffic) ? ($ipv4LogdroppedTraffic ? 'Yes' : 'No') : 'N/A'; ?></span></p>
        <p class="mediumopacity-cst">IPv6 inbound default policy: <span class="bold"><?php echo $ipv6DefaultInputPolicy ?? 'N/A'; ?></span></p>
        <p class="mediumopacity-cst">Log dropped IPv6 traffic: <span class="bold"><?php echo isset($ipv6LogdroppedTraffic) ? ($ipv6LogdroppedTraffic ? 'Yes' : 'No') : 'N/A'; ?></span></p>
        <p class="mediumopacity-cst">Log retention: <span class="bold"><?php echo $logRetention . ' days' ?? '30 days'; ?></span></p>
    </div>
</section>
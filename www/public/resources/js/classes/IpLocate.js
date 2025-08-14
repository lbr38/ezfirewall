class IpLocate {
    /**
     *  Locate an IP address using the ip-api.com API
     *  @param {string} ip - The IP address to locate
     *  @returns {Promise} - A promise that resolves with the location data or rejects with an error message
     */
    async locate(ip)
    {
        return new Promise((resolve, reject) => {
            $.ajax({
                type: "GET",
                // Call /api/ip/ endpoint which will redirect to the ip-api.com
                url: "/api/ip/" + ip,
                success: function (data, textStatus, jqXHR) {
                    /**
                     *  Retrieve and print success message
                     */
                    const result = jQuery.parseJSON(jqXHR.responseText);

                    /**
                     *  If status is not 'success', print error message
                     */
                    if (result.status != 'success') {
                        reject('Failed to retrieve location for this IP address (status: ' + result.status + '): ' + result.message);
                        return;
                    }

                    /**
                     *  Return the result
                     */
                    resolve(result);
                },
                error: function (jqXHR, textStatus, thrownError) {
                    reject('Failed to retrieve location for this IP address: ' + thrownError);
                },
            });
        });
    }

    /**
     * Locate an IP address and replace the DOM elements with the results
     * @param {} srcElements
     */
    locateReplace(srcElements)
    {
        /**
         *  Save the context of 'this' to use inside the callback
         *  This is necessary because 'this' will refer to the current element in the context of the callback function.
         */
        const self = this;

        $(srcElements).each(function () {
            const ip = $(this).attr('ip');

            /**
             *  Locate ip and get results
             */
            self.locate(ip).then((result) => {
                /**
                 *  Replace values in the DOM
                 */
                const country = result.country ? result.country : 'Unknown Country';
                const countryCode = result.countryCode ? result.countryCode : 'Unknown Country Code';
                const region = result.region ? result.region : 'Unknown Region';
                const regionName = result.regionName ? result.regionName : 'Unknown Region Name';
                const city = result.city ? result.city : 'Unknown City';
                const zip = result.zip ? result.zip : 'Unknown Zip';
                const lat = result.lat ? result.lat : 'Unknown Latitude';
                const lon = result.lon ? result.lon : 'Unknown Longitude';
                const timezone = result.timezone ? result.timezone : 'Unknown Timezone';
                const isp = result.isp ? result.isp : 'Unknown ISP';
                const org = result.org ? result.org : 'Unknown Organization';
                const as = result.as ? result.as : 'Unknown AS';

                /**
                 *  Replace values in the DOM
                 */
                $(this).find('.ip-location-country').text(country);
                $(this).find('.ip-location-country-code').text(countryCode);
                $(this).find('.ip-location-region').text(region);
                $(this).find('.ip-location-region-name').text(regionName);
                $(this).find('.ip-location-city').text(city);
                $(this).find('.ip-location-zip').text(zip);
                $(this).find('.ip-location-lat').text(lat);
                $(this).find('.ip-location-lon').text(lon);
                $(this).find('.ip-location-timezone').text(timezone);
                $(this).find('.ip-location-isp').text(isp);
                $(this).find('.ip-location-org').text(org);
                $(this).find('.ip-location-as').text(as);

                /**
                 *  Replace the flag image
                 *  Check if an asset with the country code exists
                 */
                $.get('/assets/icons/flags/' + countryCode.toLowerCase() + '.png')
                    .done(function () {
                        $(this).find('.ip-location-flag').html('<img class="country-flag-icon" src="/assets/icons/flags/' + countryCode.toLowerCase() + '.png" />');
                    }.bind(this));
            }).catch((error) => {
                /**
                 *  Print error message
                 */
                $(this).html('<img src="/assets/icons/error.svg" class="icon-np" title="' + error + '" />');
            });
        });
    }
}

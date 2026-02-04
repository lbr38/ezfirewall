/**
 *  Return GET parameters as object (array)
 */
function getGetParams()
{
    /**
     *  Get current URL and GET parameters
     */
    let url = new URL(window.location.href)
    let params = new URLSearchParams(url.search);
    let entries = params.entries();

    /**
     *  Parse and convert to object
     *  For each GET param, add key and value to the object
     */
    let array = {}
    for (let entry of entries) { // each 'entry' is a [key, value]
        let [key, val] = entry;

        /**
         *  If key ends with '[]' then it's an array
         */
        if (key.endsWith('[]')) {
            // clean up the key
            key = key.slice(0,-2);
            (array[key] || (array[key] = [])).push(val)
        /**
         *  Else it's a normal parameter
         */
        } else {
            array[key] = val;
        }
    }

    return array;
}

/**
 * Append a GET parameter to the URL but do not reload the page
 */
function appendGetParam(key, value)
{
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url.toString());
}

/**
 * Return true if the value is empty
 */
function empty(value)
{
    // Check if the value is null or undefined
    if (value == null) {
        return true;
    }

    // Check if the value is a string and is empty
    if (typeof value === 'string' && value.trim() === '') {
        return true;
    }

    // Check if the value is an empty array
    if (Array.isArray(value) && value.length === 0) {
        return true;
    }

    // Check if the value is an empty object
    if (typeof value === 'object' && Object.keys(value).length === 0) {
        return true;
    }

    // Check if the value is a number and is NaN
    if (typeof value === 'number' && isNaN(value)) {
        return true;
    }

    // If none of the above conditions are met, the value is not empty
    return false;
}

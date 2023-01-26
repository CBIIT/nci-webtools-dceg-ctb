/**
 *
 * Copyright 2022, Institute for Systems Biology
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

require.config({
    baseUrl: STATIC_FILES_URL+'js/',
    paths: {
        base: 'base',
    },
});

require([
    'base',
], function(base) {
    $(document).ready(function () {
        $("#search-save").on("click", function(e){
            $('#save_message').html('');
            if (is_input_valid(e))
                save_filters();
        });
    });



    let save_filters = function () {
        $.ajax({
            type: "post",
            url: BASE_URL + "/search_facility/save_filters",
            data: $('#save-form').serialize(),
            success: function(data) {
                $('#save_message').html('<i class="fas fa-check-circle"></i> '+data['message']);
            }
        });
    };
});

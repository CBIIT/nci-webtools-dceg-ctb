/**
 *
 * Copyright 2023, Institute for Systems Biology
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
    'base'
], function(base) {
    $(document).ready(function () {
        $("#search-save").on("click", function(e){
            $('#save_message').html('');
            let title_id = $(this).data('titleid');
            let search_title = $('#' + title_id).val()
            let form_id = $(this).data('formid');
            if (is_input_valid(search_title, e)){
                $('#save-icon').addClass('d-none');
                $('#load-icon').removeClass('d-none');
                if ($('#search-save-title').val() != search_title) {
                    $('#search-save-title').val(search_title)
                }
                save_filters(form_id);
            }
        });
    });



    let save_filters = function (form_id) {

        $.ajax({
            type: "post",
            url: BASE_URL + "/search_facility/save_filters",
            data: $('#'+form_id).serialize(),
            success: function(data) {
                $('#save-icon').removeClass('d-none');
                $('#load-icon').addClass('d-none');
                $('#close-btn').click();
                $('#general-message').html('<div class=\"border rounded p-2 mb-2 text-primary fst-italic\"><i class="fas fa-check-circle"></i> '+data['message']+'</div>');
            }
        });
    };
});

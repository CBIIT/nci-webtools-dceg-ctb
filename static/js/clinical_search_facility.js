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
    }
});

require([
    'base',
], function() {
    $(document).ready(function () {
        $("#driver-search-btn").attr("href", BASE_URL + "/search_facility/driver_search_facility"+window.location.search)
        let step = 0;
        $('#next-btn, #clinic-skip, #proceed-btn').on("click", function () {
            $('#form-clinic-' + step).addClass('d-none');
            $('#form-clinic-' + (++step)).removeClass('d-none');
            update_screen();
        });
        $('#back-btn').on("click", function () {
            $('#form-clinic-'+step).addClass('d-none');
            $('#form-clinic-'+(--step)).removeClass('d-none');
            update_screen();
        });
        let update_screen = function () {
            $('#submit-btn, #next-btn, #back-btn, #proceed-btn, #clinic-skip, #clinic-sidebar').addClass('d-none');
            if (step) {
                $('#back-btn').removeClass('d-none');
                if (step > 3) {
                    $('#submit-btn').removeClass('d-none');
                    $('#clinic-skip').addClass('d-none');
                } else {
                    $('#next-btn').removeClass('d-none');
                    $('#clinic-skip').removeClass('d-none');
                }
                $('#clinic-sidebar-buttons').addClass('d-none');
                $('#clinic-sidebar').removeClass('d-none');
            }
            else{
                $('#proceed-btn').removeClass('d-none');
                $('#clinic-sidebar-buttons').removeClass('d-none');
            }
            //update progress bar
            for (let i=0; i<6; i++){
                if (i > step)
                    $('#clinical-step-'+i).removeClass('step-active step-done');
                else if (i == step)
                    $('#clinical-step-'+i).addClass('step-active step-done');
                else {
                    $('#clinical-step-' + i).addClass('step-done');
                    $('#clinical-step-' + i).removeClass('step-active');
                }
            }
            window.scrollTo(0, 0);
        }
    });


});



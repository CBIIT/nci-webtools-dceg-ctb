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
        var step = 0;

        $('#next-btn, #proceed-btn').on("click", function () {
            $('#form-clinic-' + step).addClass('d-none');
            $('#form-clinic-' + (++step)).removeClass('d-none');
            update_screen();
        });
        $('#back-btn').on("click", function () {
            $('#form-clinic-'+step).addClass('d-none');
            $('#form-clinic-'+(--step)).removeClass('d-none');
            update_screen();
        });
        $('#clinic-skip').on("click", function () {
            $('#form-clinic-' + step).addClass('d-none');
            step=4;
            $('#form-clinic-' + (step)).removeClass('d-none');
            update_screen();
        });

        var update_screen = function () {
            $('#submit-btn, #next-btn, #back-btn, #proceed-btn, #clinic-skip').addClass('d-none');
            $('#clinic-skip').removeClass('d-none');
            if (step) {
                $('#back-btn').removeClass('d-none');
                if (step > 3) {
                    $('#submit-btn').removeClass('d-none');
                    $('#clinic-skip').addClass('d-none');
                } else {
                    $('#next-btn').removeClass('d-none');
                }
            }
            else{
                $('#proceed-btn').removeClass('d-none');
            }
            window.scrollTo(0, 0);
        }

    });


});



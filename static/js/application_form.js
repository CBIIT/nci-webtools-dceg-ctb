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
        let step = 0;
        $('.copyover').on('change', function(){
            let input_name = $(this).attr('name');
            let input_val = $(this).val();
            $(':text[name="'+input_name+'"][readonly=readonly], :input[name="'+input_name+'"][readonly=readonly]').val(input_val);
        });
        $("#next-btn, #back-btn").on("click", function () {
            $('#app-div-' + step).addClass('d-none');
            if ($(this).attr('id').startsWith('next'))
                step++;
            else
                step--;
            $('#app-div-' + step).removeClass('d-none');
            update_screen();
        });
        $("#f-agree").on("click", function(){
            $("#submit-btn").toggleClass('disabled', !$(this).is(":checked"))
        });
        let update_screen = function () {
            $('#back-btn').addClass('disabled');
            if (step) {
                $('#back-btn').removeClass('disabled');
                if (step > 4) {
                    $('#submit-btn').removeClass('d-none');
                    $('#next-btn').addClass('d-none');
                } else {
                    $('#next-btn').removeClass('d-none');
                    $('#submit-btn').addClass('d-none');
                }
            }
            window.scrollTo(0, 0);
        }
    });


});



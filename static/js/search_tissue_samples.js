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
        'datatables.net': 'lib/datatables.min',
        'datatables.bootstrap': 'lib/dataTables.bootstrap5.min',
    },
    shim: {
        'datatables.net': ['base'],
        'datatables.bootstrap': ['base']
    }
});

require([
    'base',
    'datatables.net',
    'datatables.bootstrap'
], function(base) {
    // To ensure the search is not run while the user is still actively entering the inputs
    // the system will wait for at least 1.5 seconds to see if there are any other inputs being entered
    let lastInputChangeTimeLog = 0;    // 0 indicates a reset timer
    let TIME_TO_WAIT = 1500; // 1.5 secs
    $(document).ready(function () {

        let queryString = window.location.search;
        if (queryString){
            const urlParams = new URLSearchParams(queryString);
            for(const [key, value] of urlParams.entries()){
                if(key == 'title'){
                    $('#general-message').attr('data-title',value);
                }
                else if(key.endsWith('[]')) {
                    $("input:checkbox[name='" + key + "'][value='" + value + "']").prop('checked', true);
                }
                else if (key.startsWith('age')){
                    $(":input[type='number'][name='"+key+"']").val(value);
                }
                else{
                    $("input:radio[name='"+key+"'][value='"+value+"']").prop('checked', true);
                }
            }
        }
        $('.table').DataTable({
            dom: 't',
            columns: [
                null,
                {
                    class: 'text-end'
                },
                {
                    class: 'text-end'
                },
                {
                    class: 'text-end'
                }
            ],
            ordering: false

        });

        search_samples();

        $("#search-tissue-filters input").not("#search-save-title").on("change", function () {
            lastInputChangeTimeLog = Date.now();
            setTimeout(run_search_after_sleep, TIME_TO_WAIT);
        });

        // $("#search-save").on("click", function(e){
        //     $('#save_message').html('');
        //     if (is_input_valid(e))
        //         save_filters();
        //
        // });
    });
    let run_search_after_sleep = function(){
        if (lastInputChangeTimeLog && Date.now() - lastInputChangeTimeLog > TIME_TO_WAIT){
            lastInputChangeTimeLog = 0; // reset timer
            search_samples();
        }
    };


    // let save_filters = function () {
    //     $.ajax({
    //         type: "post",
    //         url: BASE_URL + "/search_facility/save_filters",
    //         data: $('#search-tissue-form').serialize() +'&search_type=Biosample',
    //         success: function(data) {
    //             $('#save_message').html('<i class="fas fa-check-circle"></i> '+data['message']);
    //         }
    //     });
    // };
    let search_samples = function () {
        let form_inputs = $("input.form-check-input:checkbox, input.form-check-input:radio, button.btn-reset, :input[type='number']");
        $('#total-input').val('');
        $('#total-case-count').text(numberWithCommas(0));
        $('table.table').addClass('loading');
        $("#make-app-btn, #clinical-search-facility-btn, #search-save-btn").addClass('disabled')
        $.ajax({
            type: "post",
            url: BASE_URL + "/search_facility/filter_tissue_samples",
            data: $('#search-tissue-form').serialize(),
            beforeSend: function(){
                form_inputs.attr("disabled", true);
            },
            success: function (case_counts) {
                $("#make-app-btn, #clinical-search-facility-btn, #search-save-btn").removeClass('disabled');
                $('table.table.loading').removeClass('loading');
                form_inputs.attr("disabled", false);
                $('#total-case-count').text(numberWithCommas(case_counts['total']));
                $('#total-input').val(case_counts['total']);
                $('#tissue-rna-normal').text(numberWithCommas(case_counts['tissue']['rna']['normal']));
                $('#tissue-rna-tumour').text(numberWithCommas(case_counts['tissue']['rna']['tumour']));
                $('#tissue-rna-metastatic').text(numberWithCommas(case_counts['tissue']['rna']['metastatic']));
                $('#tissue-dna-normal').text(numberWithCommas(case_counts['tissue']['dna']['normal']));
                $('#tissue-dna-tumour').text(numberWithCommas(case_counts['tissue']['dna']['tumour']));
                $('#tissue-dna-metastatic').text(numberWithCommas(case_counts['tissue']['dna']['metastatic']));
                $('#tissue-ffpe-normal').text(numberWithCommas(case_counts['tissue']['ffpe']['normal']));
                $('#tissue-ffpe-tumour').text(numberWithCommas(case_counts['tissue']['ffpe']['tumour']));
                $('#tissue-ffpe-metastatic').text(numberWithCommas(case_counts['tissue']['ffpe']['metastatic']));
                $('#blood-serum').text(numberWithCommas(case_counts['blood']['serum']));
                $('#blood-dna').text(numberWithCommas(case_counts['blood']['dna']));
                $('#clinical-search-facility-btn').attr('href', BASE_URL + "/search_facility/clinical_search_facility?" + $('#search-tissue-form').serialize())
                $('#general-message').html($('#general-message').data('title')?"<div class=\"border rounded p-2 mb-2 text-primary fst-italic\"><i class=\"fas fa-check-circle\"></i> Search '"+$('#general-message').data('title')+"' is loaded</div>":"")
            }
        });
    };
});

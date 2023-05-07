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
    $(document).ready(function () {
        let my_search_tbl = $('#saved_searches_tbl').DataTable({
            scrollX: true,
            ordering: false,
            ajax: {
                url: BASE_URL + "/search_facility/get_search_list/",
                dataSrc: ''
            },
            columns: [
                {
                    class: 'text-end',
                    render: function (data, type, row, meta) {
                        let search_type_url;
                        if (row.search_type == 'Biosample') {
                            search_type_url = 'search_tissue_samples';
                        } else if (row.search_type == 'Clinical') {
                            search_type_url = 'search_clinical';
                        } else {
                            search_type_url = 'driver_search_facility';
                        }
                        let search_url = BASE_URL + "/search_facility/" + search_type_url + row.filter_encoded_url + '&title='+row.name;
                        return "<a href='" + search_url + "'>" + row.name + "</a>";
                    }
                },
                {
                    data: 'search_type',
                    class: 'text-end',
                },
                {
                    data: 'case_count',
                    type: 'num',
                    class: 'text-end',
                    render: $.fn.dataTable.render.number(',', null)
                },
                {
                    class: 'date-col text-end',
                    data: 'saved_date',
                    type: 'date'
                },

                // {
                //     class: 'text-center',
                //     render: function (data, type, row, meta) {
                //         let driver_search_url = BASE_URL + "/search_facility/driver_search_facility/" + row.filter_encoded_url;
                //         return "<a href='" + driver_search_url + "'>Driver Search <i class=\"fa-solid fa-angle-right\"></i></a>"
                //     },
                //     orderable: false
                // },
                {
                    class: 'text-center',
                    render: function (data, type, row, meta) {
                        return "<a class='delete-search-btn' href='#' data-filter-id='" + row.filter_id + "'><i class='fa-solid fa-trash-can'></i></a>";
                    },
                    // orderable: false
                },
            ]
        });
        $('#saved_searches_tbl tbody').on('click', '.delete-search-btn', function () {
            delete_filter($(this).data('filter-id'));
        });

        let delete_filter = function (filter_id) {
            $.ajax({
                type: "post",
                url: BASE_URL + "/search_facility/delete_filters/" + filter_id + "/",
                success: function (data) {
                    my_search_tbl.ajax.reload();
                    $('#delete_success_message').text('');
                    $('#delete_error_message').text('');
                    if (data.success) {
                        $('#delete_success_message').text(data.success);
                    } else {
                        $('#delete_error_message').text(data.error);
                    }
                }
            });
        };
    });
});
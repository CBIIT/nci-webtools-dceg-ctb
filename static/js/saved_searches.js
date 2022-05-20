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
        $('#saved_searches_tbl').DataTable();
    });

});
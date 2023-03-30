###
# Copyright 2015-2022, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###
from django.conf import settings
from django.db import connection


def build_clinical_where_clause(filters=None, clinical_alias='cl', sample_alias='s'):
    where_clause_items = []
    if filters:
        op_type = filters.get('op_type')
        pt_status_a = filters.get('pt_status_a[]')
        pt_status_b = filters.get('pt_status_b[]')
        reg_node = filters.get('reg_node[]')
        ajcc_a = filters.get('ajcc_a[]')
        ajcc_b = filters.get('ajcc_b[]')
        treat_radio = filters.get('treat_radio')
        tsh_supress = filters.get('tsh_supress')
        clinic_outcome = filters.get('clinic_outcome')

        if op_type and op_type != 'any':
            where_clause_items.append(
                '{clinical_alias}.operation_type = \'{op}\''.format(clinical_alias=clinical_alias, op=(
                    "total thyroidectomy" if op_type == "total" else "less than total")))
        pt_status_items = []
        if pt_status_a:
            pt_status_a_items = []
            for t_status in pt_status_a:
                if len(t_status) > 2:
                    pt_status_a_items.append(
                        '{clinical_alias}.classification_tumour LIKE \'{pt1}%{pt2}%\''.format(
                            clinical_alias=clinical_alias, pt1=t_status[:2], pt2=t_status[2:])
                    )
                else:
                    pt_status_a_items.append(
                        '( {clinical_alias}.classification_tumour LIKE \'{t_status}%\''.format(
                            clinical_alias=clinical_alias, t_status=t_status)
                        + '\n\t\tAND {clinical_alias}.classification_tumour NOT LIKE \'%a%\''.format(
                            clinical_alias=clinical_alias)
                        + '\n\t\tAND {clinical_alias}.classification_tumour NOT LIKE \'%b%\' )'.format(
                            clinical_alias=clinical_alias)
                    )

            pt_status_or_clause = '\n\t\tOR '.join(pt_status_a_items)
            pt_status_items.append("( {pt_status_or_clause} )\n\t\tAND {sample_alias}.diagnosis != 'MTC'".format(
                pt_status_or_clause=pt_status_or_clause, sample_alias=sample_alias))
        if pt_status_b:
            pt_status_b_items = []
            for t_status in pt_status_b:
                if len(t_status) > 2:
                    pt_status_b_items.append(
                        '{clinical_alias}.classification_tumour like \'{pt1}%{pt2}%\''.format(
                            clinical_alias=clinical_alias, pt1=t_status[:2], pt2=t_status[2:])
                    )
                else:
                    pt_status_b_items.append(
                        '( {clinical_alias}.classification_tumour LIKE \'{t_status}%\''.format(
                            clinical_alias=clinical_alias, t_status=t_status)
                        + '\n\t\tAND {clinical_alias}.classification_tumour NOT LIKE \'%a%\''.format(
                            clinical_alias=clinical_alias)
                        + '\n\t\tAND {clinical_alias}.classification_tumour NOT LIKE \'%b%\' )'.format(
                            clinical_alias=clinical_alias)
                    )
            pt_status_or_clause = '\n\t\tOR '.join(pt_status_b_items)
            pt_status_items.append("( {pt_status_or_clause} )\n\t\tAND {sample_alias}.diagnosis = 'MTC'".format(
                pt_status_or_clause=pt_status_or_clause, sample_alias=sample_alias))
        if pt_status_items:
            where_clause_items.append('\n\t\tOR '.join(pt_status_items))
        if reg_node:
            reg_node_items = []
            for n_status in reg_node:
                if len(n_status) > 2:
                    reg_node_items.append(
                        '{clinical_alias}.classification_normal like \'{pt1}%{pt2}%\''.format(
                            clinical_alias=clinical_alias, pt1=n_status[:2], pt2=n_status[2:])
                    )
                else:
                    reg_node_items.append(
                        '{clinical_alias}.classification_normal = \'{n_status}\''.format(clinical_alias=clinical_alias,
                                                                                         n_status=n_status)
                    )

            where_clause_items.append('\n\t\tOR '.join(reg_node_items))
        ajcc_items = []
        if ajcc_a:
            ajcc_items.append(
                "( {clinical_alias}.stage IN ('{stage_clause}') AND {sample_alias}.diagnosis != 'MTC' )".format(
                    clinical_alias=clinical_alias, stage_clause=("','".join(ajcc_a)), sample_alias=sample_alias))
        if ajcc_b:
            ajcc_items.append(
                "( {clinical_alias}.stage IN ('{stage_clause}') AND {sample_alias}.diagnosis = 'MTC' )".format(
                    clinical_alias=clinical_alias, stage_clause="','".join(ajcc_b), sample_alias=sample_alias))
        if ajcc_items:
            where_clause_items.append('\n\t\tOR '.join(ajcc_items))
        if treat_radio and treat_radio != 'neither':
            where_clause_items.append('{clinical_alias}.rit = {tr_radio}'.format(
                clinical_alias=clinical_alias, tr_radio=('TRUE' if treat_radio == 'yes' else 'FALSE')))
        if tsh_supress and tsh_supress != 'neither':
            where_clause_items.append(
                '{clinical_alias}.tsh_suppression = {tsh_suppression}'.format(
                    clinical_alias=clinical_alias, tsh_suppression=('TRUE' if tsh_supress == 'yes' else 'FALSE')))
        if clinic_outcome and clinic_outcome != 'neither':
            where_clause_items.append(
                '{clinical_alias}.relapse = {clinic_outcome}'.format(clinical_alias=clinical_alias, clinic_outcome=(
                    'TRUE' if clinic_outcome == 'yes' else 'FALSE')))
    if len(where_clause_items):
        where_clause = '({})'.format(')\n\t\tAND ('.join(where_clause_items))
    else:
        where_clause = 'TRUE'
    return where_clause


def build_sample_where_clause(sample_filters=None, donor_alias='d', sample_alias='s'):
    where_clause_items = []
    if sample_filters:
        diagnosis = sample_filters.get('diagnosis[]')
        sample_type = sample_filters.get('sample_type[]')
        country = sample_filters.get('country')
        dosemetry = sample_filters.get('dosemetry[]')
        sample_origin = sample_filters.get('sample_origin[]')
        patient_residency = sample_filters.get('patient_residency')
        dob = sample_filters.get('dob')
        patient_gender = sample_filters.get('patient_gender')
        age_at_operation_min = sample_filters.get('age_at_operation_min')
        age_at_operation_max = sample_filters.get('age_at_operation_max')
        age_at_exposure_min = sample_filters.get('age_at_exposure_min')
        age_at_exposure_max = sample_filters.get('age_at_exposure_max')
        if diagnosis:
            where_clause_items.append(
                '{sample_alias}.diagnosis in (\'{diagnosis_list}\')'.format(sample_alias=sample_alias,
                                                                            diagnosis_list=('\', \''.join(diagnosis))))
        if sample_type:
            has_ffpe_filter = False
            sample_type_vals = []
            for item in sample_type:
                if item == 'FFPE':
                    has_ffpe_filter = True
                else:
                    sample_type_vals.append(item)
            sample_type_clause = ''
            if sample_type_vals:
                sample_type_clause = '{sample_alias}.subtype in (\'{subtype_list}\')\n'.format(
                    sample_alias=sample_alias, subtype_list=('\', \''.join(sample_type_vals)))
            if has_ffpe_filter:
                sample_type_clause += (('OR ' if sample_type_clause else '') + '{sample_alias}.subtype is null'.format(
                    sample_alias=sample_alias))
            where_clause_items.append(sample_type_clause)
        if country and country != 'both':
            where_clause_items.append(
                "LOWER({donor_alias}.country_at_accident) = '{country_list}'".format(donor_alias=donor_alias,
                                                                                     country_list=country.lower()))
        if dosemetry:
            dosimetry_items = []
            for item in dosemetry:
                if item == '100mGy':
                    dosimetry_items.append('{donor_alias}.dosimetry < 100 AND {donor_alias}.dosimetry >= 0'.format(donor_alias=donor_alias))
                elif item == '100mGy500mGy':
                    dosimetry_items.append(
                        '( {donor_alias}.dosimetry >= 100 AND {donor_alias}.dosimetry <= 500 )'.format(
                            donor_alias=donor_alias))
                elif item == '500mGy':
                    dosimetry_items.append('{donor_alias}.dosimetry > 500'.format(donor_alias=donor_alias))
                else:
                    # Unknown
                    dosimetry_items.append('{donor_alias}.dosimetry IS NULL'.format(donor_alias=donor_alias))
            dosimetry_clause = '({})'.format('\nOR '.join(dosimetry_items))
            where_clause_items.append(dosimetry_clause)
        if sample_origin:
            has_blood_filter = False
            sample_origin_vals = []
            for item in sample_origin:
                if item == 'blood':
                    has_blood_filter = True
                else:
                    sample_origin_vals.append(item)
            sample_origin_clause = ''
            if sample_origin_vals:
                sample_origin_clause = '{sample_alias}.tnm_type in (\'{sample_org_list}\')'.format(
                    sample_alias=sample_alias, sample_org_list=('\', \''.join(sample_origin_vals)))
            if has_blood_filter:
                sample_origin_clause += (('OR ' if sample_origin_clause else '') + '{sample_alias}.tnm_type is null'.format(
                    sample_alias=sample_alias))
            where_clause_items.append(sample_origin_clause)
        if patient_residency and patient_residency != 'both':
            patient_residency_clause = "LOWER({donor_alias}.oblast_at_accident) {patient_res_bool} IN ({patient_res_list})".format(
                donor_alias=donor_alias,
                patient_res_bool=('' if patient_residency == 'exposed' else 'NOT'),
                patient_res_list="'kaluga','tula','orel','bryansk','kiev','rovno','chercassy','zhytomyr','chernigov','sumy','pripyat'"
            )
            where_clause_items.append(patient_residency_clause)
        if dob and dob != 'both':
            where_clause_items.append('age_category = {}'.format(', '.join(dob)))
        if patient_gender and patient_gender != 'both':
            where_clause_items.append("gender = '{}'".format(patient_gender))
        age_at_operation_items = []
        if age_at_operation_min:
            age_at_operation_items.append(
                'age_at_first_operation >= {age_at_operation_min}'.format(age_at_operation_min=age_at_operation_min))
        if age_at_operation_max:
            age_at_operation_items.append(
                'age_at_first_operation <= {age_at_operation_max}'.format(age_at_operation_max=age_at_operation_max))
        if len(age_at_operation_items):
            where_clause_items.append(' AND '.join(age_at_operation_items))
        age_at_exposure_items = []
        if age_at_exposure_min:
            age_at_exposure_items.append(
                'age_at_exposure >= {age_at_exposure_min}'.format(age_at_exposure_min=age_at_exposure_min))
        if age_at_exposure_max:
            age_at_exposure_items.append(
                'age_at_exposure <= {age_at_exposure_max}'.format(age_at_exposure_max=age_at_exposure_max))
        if len(age_at_exposure_items):
            where_clause_items.append(' AND '.join(age_at_exposure_items))
    if len(where_clause_items):
        where_clause = '({})'.format(')\n\t\t\tAND ('.join(where_clause_items))
    else:
        where_clause = 'TRUE'
    return where_clause


def get_driver_case_counts(filters=None):

    sample_clause = build_sample_where_clause(filters, 'd', 's') if filters else 'TRUE'
    where_clause = build_clinical_where_clause(filters, 'cl', 's') if filters else 'TRUE'
    query_template = '''
        SELECT dr.gene, COUNT(DISTINCT(d.id))
        FROM `donors_donor` as d
        {sample_clin_join}
        JOIN `donors_driver` as dr
        ON dr.patient_uid = d.patient_uid
        WHERE {sample_clause}
        AND {where_clause} 
        GROUP BY dr.gene
        ;
    '''
    sample_clin_join = '''
        JOIN `donors_sample` as s
        ON d.patient_id = s.donor_id
        JOIN `donors_clinical_treatment` as cl
        ON cl.patient_id = d.patient_id
    '''

    count_query = query_template.format(sample_clin_join=sample_clin_join, where_clause=where_clause,
                                        sample_clause=sample_clause)
    total_avail_count_query = query_template.format(sample_clin_join='', where_clause='TRUE', sample_clause='TRUE')
    # print(count_query)
    # print(total_avail_count_query)
    counts = {
    }
    total_filtered_case_count = 0
    with connection.cursor() as cursor:
        cursor.execute(total_avail_count_query)
        total_avail_case_counts = cursor.fetchall()
        for row in total_avail_case_counts:
            if row[0].startswith('Not'):
                gene_name = "NYI"
            else:
                gene_name = row[0].replace('.', '_').replace('/', '_')
            if gene_name not in counts:
                counts[gene_name] = {}
            counts[gene_name]['total'] = row[1]
        cursor.execute(count_query)
        driver_case_counts = cursor.fetchall()
        for row in driver_case_counts:
            if row[0].startswith('Not'):
                gene_name = "NYI"
            else:
                gene_name = row[0].replace('.', '_').replace('/', '_')
            counts[gene_name]['filtered'] = row[1]
            total_filtered_case_count += row[1]
    return total_filtered_case_count, counts


def is_default_filter(filters=None):
    # print(filters)
    # filters.pop('total', None)
    is_default = True
    for k, v in filters.items():
        if k != 'csrfmiddlewaretoken' and settings.BLANK_TISSUE_FILTERS.get(k, None) != v:
            is_default = False
            break
    for k, v in settings.BLANK_TISSUE_FILTERS.items():
        if filters.get(k, 'both') != v:
            is_default = False
    return is_default


def get_sample_case_counts(filters=None):
    case_counts = {
        'tissue': {
            'rna': {
                'normal': 0,
                'tumour': 0,
                'metastatic': 0
            },
            'dna': {
                'normal': 0,
                'tumour': 0,
                'metastatic': 0
            },
            'ffpe': {
                'normal': 0,
                'tumour': 0,
                'metastatic': 0
            }
        },
        'blood': {
            'dna': 0,
            'serum': 0
        },
        'total': 0
    }
    if is_default_filter(filters):
        case_counts = settings.BLANK_TISSUE_FILTER_CASE_COUNT
    else:
        where_clause = build_sample_where_clause(filters, 'd', 's')

        query_template = '''
            SELECT {group_select_clause}COUNT(DISTINCT(d.patient_id))
            FROM `donors_donor` AS d 
            JOIN `donors_sample` AS s
            ON d.patient_id = s.donor_id
            WHERE {where_clause}
            {group_clause};
        '''
        group_select_clause = 's.subtype, s.tnm_type, '
        group_clause = 'GROUP BY s.subtype, s.tnm_type'

        total_count_query = query_template.format(group_select_clause='', where_clause=where_clause, group_clause='')
        grouped_count_query = query_template.format(group_select_clause=group_select_clause, where_clause=where_clause,
                                                    group_clause=group_clause)
        # print(total_count_query)
        # print(grouped_count_query)
        with connection.cursor() as cursor:
            cursor.execute(total_count_query)
            case_counts['total'] = cursor.fetchone()[0]
            cursor.execute(grouped_count_query)
            results = cursor.fetchall()

            for row in results:
                subtype = 'ffpe' if row[0] is None else row[0]
                tnm_type = row[1]
                count = row[2]
                sample_type = 'blood' if tnm_type is None else 'tissue'
                if sample_type in case_counts and subtype in case_counts.get(sample_type):
                    if tnm_type is None:
                        case_counts[sample_type][subtype] = count
                    elif tnm_type in case_counts.get(sample_type).get(subtype):
                        case_counts[sample_type][subtype][tnm_type] = count
    return case_counts


def get_clinical_case_counts(filters):
    where_clause = build_clinical_where_clause(filters, 'cl', 'samp')
    sample_clause = build_sample_where_clause(filters, 'd', 's')

    query_template = '''
        SELECT COUNT(DISTINCT(samp.id))
        FROM (
            SELECT d.id, d.patient_id, d.diagnosis
            FROM `donors_donor` as d
            JOIN `donors_sample` as s
            ON d.patient_id = s.donor_id
            WHERE {sample_clause}
        ) AS samp
        JOIN `donors_clinical_treatment` as cl
        ON cl.patient_id = samp.patient_id
        WHERE {where_clause}
        ;
    '''
    total_count_query = query_template.format(where_clause=where_clause, sample_clause=sample_clause)
    # print(total_count_query)
    with connection.cursor() as cursor:
        cursor.execute(total_count_query)
        total_case_count = cursor.fetchone()[0]
    return total_case_count

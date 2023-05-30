from aspen import standardize_cols, expand_aspen_history
import pandas as pd
import xlsxwriter
import warnings

warnings.simplefilter('ignore')


def parse_combined_histories(history_xlsx: str):
    raw_aspen_df = pd.read_excel(history_xlsx, sheet_name="Clean Aspen Manifest")
    standardized = standardize_cols(raw_aspen_df=raw_aspen_df)
    aspen_df = expand_aspen_history(standardized_aspen_df=standardized)
    icare_df = pd.read_excel(history_xlsx, sheet_name="I-CARE Scraper")
    print('Excel loaded.')
    return aspen_df, icare_df


def compare_histories(aspen_df, icare_df):
    errors = icare_df.loc[icare_df['icare_status'].isin(['ERROR: Multiple I-CARE Matches Found.',
                                                         'ERROR: No I-CARE Matches Found.'])]
    errors['d_str'] = errors['DOB'].apply(lambda d: d.strftime("%m-%d-%Y"))
    errors['unique_id'] = errors['LastName'] + ":" + errors['FirstName'] + ":" + errors['d_str']
    icare_df = icare_df.loc[~icare_df['icare_status'].isin(['invalid', 'Invalid'])]

    combined_history = pd.merge(aspen_df, icare_df, how='outer')
    combined_history = combined_history.loc[
        ~combined_history['icare_status'].isin(['ERROR: Multiple I-CARE Matches Found.',
                                                'ERROR: No I-CARE Matches Found.'])]
    combined_history['d_str'] = combined_history['DOB'].apply(lambda d: d.strftime("%m-%d-%Y"))
    combined_history['unique_id'] = combined_history['LastName'] + ":" + combined_history['FirstName'] + ":" + combined_history['d_str']
    combined_history.loc[combined_history['unique_id'].isin(errors['unique_id']), 'icare_status'] = 'unknown'
    combined_history['icare_status'] = combined_history['icare_status'].fillna('compliant')
    combined_history['aspen_status'] = combined_history['aspen_status'].fillna('unknown')

    def combine_status(row):
        if row['aspen_status'] == row['icare_status']:
            return row['icare_status']
        elif row['icare_status'] == 'compliant' or row['aspen_status'] == 'compliant':
            return "compliant"
        else:
            return 'overdue'

    combined_history['combined_status'] = combined_history.apply(combine_status, axis=1)
    print("Shot history comparison complete.")
    return combined_history


def excel_output(combined_history_df: pd.DataFrame, output_filename):
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    # Light red fill with dark red text.
    format1 = writer.book.add_format({'bg_color': '#FFC7CE',
                                      'font_color': '#9C0006'})

    # Light yellow fill with dark yellow text.
    format2 = writer.book.add_format({'bg_color': '#FFEB9C',
                                      'font_color': '#9C6500'})

    # Green fill with dark green text.
    format3 = writer.book.add_format({'bg_color': '#C6EFCE',
                                      'font_color': '#006100'})

    current_row = 1
    for patient in combined_history_df['unique_id'].drop_duplicates().to_list():
        patient_df = combined_history_df.loc[combined_history_df['unique_id'] == patient]
        patient_pivot = patient_df.set_index('vaccine')[['aspen_status', 'icare_status', 'combined_status',
                                                         'overdue date (via i-care)']].T
        patient_pivot.to_excel(writer, sheet_name='Sheet1', startrow=current_row, header=True, index=True)
        writer.sheets['Sheet1'].write_string(current_row, 0,
                                             f"{patient.split(':')[1]} {patient.split(':')[0]} - {patient.split(':')[2]}")
        writer.sheets['Sheet1'].conditional_format(current_row + 3, 1, current_row + 3, patient_pivot.shape[1],
                                                   {'type': 'text',
                                                    'criteria': 'containing',
                                                    'value': 'unknown',
                                                    'format': format2})
        writer.sheets['Sheet1'].conditional_format(current_row + 3, 1, current_row + 3, patient_pivot.shape[1],
                                                   {'type': 'text',
                                                    'criteria': 'containing',
                                                    'value': 'overdue',
                                                    'format': format1})
        writer.sheets['Sheet1'].conditional_format(current_row + 3, 1, current_row + 3, patient_pivot.shape[1],
                                                   {'type': 'text',
                                                    'criteria': 'containing',
                                                    'value': 'compliant',
                                                    'format': format3})
        current_row += patient_pivot.shape[0] + 2
    writer.sheets['Sheet1'].autofit()
    writer.save()
    print('Excel comparison doc created.')


if __name__ == '__main__':
    aspen, icare = parse_combined_histories("input/YCCS Innovations (NO COVID) 05-25-2023 (1).xlsx")
    history_df = compare_histories(aspen_df=aspen, icare_df=icare)
    excel_output(history_df, 'YCCSInnovations052523.xlsx')

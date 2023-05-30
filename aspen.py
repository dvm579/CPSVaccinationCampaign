import pandas as pd


def standardize_cols(raw_aspen_df):
    standard_cols = {'LastName': 'LastName', 'FirstName': 'FirstName', 'DOB': 'DOB', 'MMR': "Measles, Mumps, Rubella",
                     'Chicken Pox': 'Varicella', 'DTP or DTaP': 'DtaP', 'Hep B': 'Hepatitis B',
                     'Hib': 'Haemophilus influenzae type B', 'IPV/ Polio': 'Poliomyelitis', 'COVID-19': 'COVID-19',
                     'PCV': 'Pneumococcal Conjugate', 'Tdap': 'Tdap', 'Meningitis': 'Meningococcal Disease'}

    for col in standard_cols.keys():
        if col not in raw_aspen_df.columns:
            raw_aspen_df[col] = 'Unknown'
    standardized_aspen_df = raw_aspen_df.rename(columns=standard_cols)

    return standardized_aspen_df


def expand_aspen_history(standardized_aspen_df: pd.DataFrame):
    aspen_expanded_df = standardized_aspen_df.melt(id_vars=['LastName', 'FirstName', 'DOB'], value_vars=['DtaP',
        'Hepatitis B','Haemophilus influenzae type B', 'Meningococcal Disease', 'Measles, Mumps, Rubella',
        'Pneumococcal Conjugate','Tdap', 'Varicella', 'Poliomyelitis', 'COVID-19'],
                                                   var_name='vaccine',
                                                   value_name="aspen_status")

    aspen_expanded_df = aspen_expanded_df.dropna(subset=['aspen_status'])

    aspen_expanded_df['aspen_status'] = aspen_expanded_df['aspen_status']\
        .apply(lambda x: 'overdue' if str(x).lower() in ['no', 'false'] else 'compliant')

    return aspen_expanded_df
    

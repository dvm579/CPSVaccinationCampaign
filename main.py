import icare
import aspen
import compare
import packets
import os
from datetime import date


def icare_history(manifest_csv: str):
    patient_df = icare.manifest_to_icare(manifest_csv)
    history = icare.generate_icare_history(patient_df)
    history.to_csv(path_or_buf=f'output/scraper-out/{os.path.splitext(os.path.basename(manifest_csv))}-out.csv')
    os.remove(manifest_csv)


def output_packets_and_comparison(combined_history_xlsx: str,
                                  schoolname: str,
                                  eventdate: list[date],
                                  eventtimestr: str,
                                  downloadpdfs=False,
                                  printpdfs=False):

    aspen, icare = compare.parse_combined_histories(combined_history_xlsx)
    history_df = compare.compare_histories(aspen_df=aspen, icare_df=icare)

    output_dir = packets.packets(combined_history_df=history_df,
                                 schoolname=schoolname,
                                 eventdate=eventdate,
                                 eventtimestr=eventtimestr,
                                 downloadpdfs=downloadpdfs,
                                 printpdfs=printpdfs)

    compare.excel_output(combined_history_df=history_df,
                         output_filename=os.path.join('output', 'packets', output_dir, f"{schoolname}.xlsx"))


if __name__ == '__main__':
    # STEP 1: CLEAN AND COMBINE ASPEN DATA INTO MANIFEST TEMPLATE, DOWNLOAD AS CSV
    # STEP 2: CREATE I-CARE HISTORY (use fx below)
    icare_history("input/curie.csv")

    # STEP 3: UPLOAD TO SHEET TITLED "I-CARE Scraper" IN ORIGINAL GSHEET
    # STEP 4: FIX I-CARE ERRORS IN-PLACE ON "I-CARE Scraper" SHEET. (DELETE ERROR ROWS ONLY IF STUDENT IS FOUND)
    # STEP 5: DOWNLOAD MANIFEST XLSX
    # STEP 6: GENERATE PACKETS AND COMPARISON EXCEL (use fx below)
    output_packets_and_comparison(combined_history_xlsx="input/Gage Park 05-30-2023 Clean Manifest.xlsx",
                                  schoolname="Gage Park HS",
                                  eventdate=[date(2023, 5, 30)],
                                  eventtimestr="10:00AM - 1:00PM",
                                  downloadpdfs=False,
                                  printpdfs=False)

from benchmark_uded_fusion_fixed import main

if __name__ == '__main__':
    try:
        main()
    except KeyError as exc:
        # benchmark_uded_fusion_fixed writes all CSV/JSON results before a final
        # diagnostic print that currently asks for the legacy column name
        # 'ODS_selection'. Preserve the completed results and exit cleanly.
        if 'ODS_selection' in str(exc):
            print('NONFATAL_FINAL_PRINT_KEYERROR:', exc, flush=True)
            print('UDED_FUSION_FIXED_V2_RESULTS_SAVED', flush=True)
        else:
            raise

"""
Tools to read in data from the Census Bureau's replicate weights files and 
compute estimates and MOEs based on that data. This is based on their data
structure and documentation as of May 2017.
documentation: https://census.gov/programs-surveys/acs/technical-documentation/variance-tables.html
data: https://census.gov/programs-surveys/acs/data/variance-tables.html
"""

import numpy as np
import pandas as pd
import multiprocessing as mp


SUMMARY_LEVELS = {
    "united states": "010",
    "us": "010",
    "state": "040",
    "county": "050",
    "county subdivision": "060",
    "tract": "140",
    "block group": "150",
    "bg": "150",
    "place": "160",
    "american indian area": "250",
    "metropolitan statistical area": "310",
    "micropolitan statistical area": "310",
    "msa": "310",
    "congressional district": "500",
    "congress": "500",
    "5-digit zip code tabulation area": "860",
    "zcta": "860",
    "zip": "860",
}


# cenpy.moe.replicate(func, years, level, *[vars], return_replicates = True):
# replicates  = fetch_replicates_from_varlist(*vars)
# results = apply_func_to_replicate_table(func, replicates)
# return results


def read_replicate_file(fname):
    """
    Convert an ACS Variance Replicate Table into a hierarchical dataframe. See
    get_replicate_data for similar functionality.

    Accepts:
        -File name of .csv downloaded from Census website
        -File name of .gz downloaded from Census website
        -Complete URL to .gz file on census website, e.g.:
         https://www2.census.gov/programs-surveys/acs/replicate_estimates/2015/data/5-year/040/B03002.csv.gz
    
    documentation: https://census.gov/programs-surveys/acs/technical-documentation/variance-tables.html
    data: https://census.gov/programs-surveys/acs/data/variance-tables.html
    
    Parameters
    ----------
    fname:  str
            Multiple options available:
            -File name of .csv downloaded from Census website
            -File name of .gz downloaded from Census website
            -Complete URL to .gz file on census website

    Returns
    -------
    Pandas hierarchical dataframe, where the first level is: estimates, moes,
    ses, replicate1, replicate2, ..., replicate80; the second level is the
    attribute columns: total pop, count Hispanic, count in poverty, etc. The
    rows are the geographic areas (e.g., tracts or counties or ...).    
    """

    table = pd.read_csv(
        fname,
        dtype={
            "TBLID": str,
            "GEOID": str,
            "NAME": str,
            "ORDER": str,
            "TITLE": str,
            "CME": str,
        },
        encoding="latin-1",
    )

    # Keep only rows that have a GEOID (remove meta-data rows)
    table = table[table["GEOID"].notna()]

    table.loc[table.ORDER.str.len() == 1, "ORDER"] = (
        "00" + table.loc[table.ORDER.str.len() == 1, "ORDER"]
    )
    table.loc[table.ORDER.str.len() == 2, "ORDER"] = (
        "0" + table.loc[table.ORDER.str.len() == 2, "ORDER"]
    )

    table["variable"] = table.TBLID + "_" + table.ORDER
    table = table.drop(["TBLID", "NAME", "ORDER", "CME", "TITLE"], axis=1)
    table = table.pivot(index="GEOID", columns="variable")
    table.columns.names = ["categories", "variables"]
    # Standardize the names of the columns because the ACB's 2014 tables have
    # lowercase titles while others are uppercase.
    table = table.rename(columns = {"estimate":"ESTIMATE", 
                                    "moe": "MOE",
                                     "se": "SE"})
    return table


def get_replicate_data(fnames, columns=[], geos=[]):
    """
    Read specific columns and geographies from ACS Variance Replicate Tables
    into a hierarchical dataframe. This script will subset from the raw Census
    provided CSV files. 
    
    Known issue: tract or block group files from different states will 
                 fail (only relevant for tract or block groups).
    Note: see read_replicate_file() and get_replicate_data_api() for 
          similar functionality.
    
    documentation: https://census.gov/programs-surveys/acs/technical-documentation/variance-tables.html
    data: https://census.gov/programs-surveys/acs/data/variance-tables.html
    
    Parameters
    ----------
    fnames:     list
                List containing files names of CSVs downloaded from Census
                website. Cannot mix files of different geography types (e.g.,
                cannot mix tracts and counties). 

    columns:    list
                List of the column names to select; in the format TBLID_ORDER,
                e.g., B03002_009 for table B03002 and variable 9 (note: always 
                three digits after the _). If empty list (default), then keep 
                all columns from all files in fnames.

    geos:       list
                List of the GEOIDs to select. If an empty list 
                (default), then keep all GEOIDs from all files in fnames.

    Returns
    -------
    Pandas hierarchical dataframe, where the first level is: estimates, moes,
    ses, replicate1, replicate2, ..., replicate80; the second level is the
    attribute columns: total pop, count Hispanic, count in poverty, etc. The
    rows are the geographic areas (e.g., tracts or counties or ...). Note that
    rows and columns follow the order of the geos and columns parameters when
    appropriate.
    """

    df = pd.DataFrame()
    # read files and select the requested rows and columns
    for fname in fnames:

        print(fname)
        table = read_replicate_file(fname)
        # print(table.columns.levels)

        if not geos and not columns:  # keep all columns and all GEOIDs
            pass
        elif not geos:  # keep some columns and all GEOIDs
            current_cols = list(
                set(columns).intersection(set(table.columns.levels[1]))
            )  # user's columns in this table
            table = table.loc[:, (slice(None), current_cols)]
        elif set(table.index.values).intersection(
            geos
        ):  # need at least one geos value in index to avoid error
            if not columns:  # keep all columns and some GEOIDs
                current_geos = list(
                    set(geos).intersection(set(table.index))
                )  # user's GEOIDs in this table
                table = table.loc[current_geos, :]
            else:  # keep some columns and some GEOIDs
                current_geos = list(
                    set(geos).intersection(set(table.index))
                )  # user's GEOIDs in this table
                current_cols = list(
                    set(columns).intersection(set(table.columns.levels[1]))
                )  # user's columns in this table
                table = table.loc[current_geos, (slice(None), current_cols)]
        else:  # skip when no geos values in index
            continue
        # The code can handle multiple tables (i.e., adding new columns) but
        # not multiple state files (i.e., adding new rows); this is only
        # relevant for tracts and block groups. The fix seems to involve a
        # line like:
        # df = df.combine_first(table)
        # instead of pd.concat(), but combine_first() does not smoothly
        # handle multiindex dataframes. Since reading replicate tables is at
        # the core of this whole module, I want to have a more robust test
        # suite before changing this.
        df = pd.concat([df, table], axis=1)

    # get row and column ordering to match input ordering
    ## top level column ordering
    cat_cols = table.columns.levels[0].values
    df_cols = df.columns.levels[0].values
    df = df.reindex(columns=cat_cols, level=0)
    ## put actual columns available in replicates data into order of columns attribute
    if columns:
        df = df.reindex(columns=columns, level=1)
        df.columns = df.columns.remove_unused_levels()  # cleans out unused column names
        missing_cols = list(set(columns).difference(set(df.columns.levels[1])))
        if missing_cols:
            print(
                "WARNING: the following column(s) not found in fnames files:",
                list(missing_cols),
            )
    ## put rows in order of geos
    if geos:
        missing_geos = list(set(geos).difference(set(df.index)))
        df = df.reindex(geos)  # this will also insert NaN rows when a GEOID not in df
        if missing_geos:
            print(
                "WARNING: the following geographic area(s) not found in fnames files:",
                missing_geos,
            )
    return df


def get_replicate_data_api(tables, year, scale, state=None, columns=[], geos=[]):
    """
    Pull specific columns and geographies from the Census Bureau's ACS
    Variance Replicate Table website, and read them into a hierarchical
    dataframe. This script will subset from the raw Census provided CSV files.
    
    Note: see read_replicate_file() and get_replicate_data() for similar 
          functionality.

    documentation: https://census.gov/programs-surveys/acs/technical-documentation/variance-tables.html
    data: https://census.gov/programs-surveys/acs/data/variance-tables.html
    
    TODO: Modify functionality to only require year, columns and geos.

    Parameters
    ----------
    tables:     list
                List containing table names to download. This is just the
                table name without geographic or column extensions. Example:
                'B03002'.

    year:       str or int
                Year of the data to download.

    scale:      str
                Spatial scale to download. Can be the "summary level code"
                (e.g., '140') or the name (e.g., 'tract'). See SUMMARY_LEVELS
                dictionary for currently available options. Case insensitive.

    state       str
                FIPS code (as string) of state to download. Only
                applicable for summary levels 140 (tract) and 150 (block
                group); ignored for other summary levels. Note: use geos 
                parameter to select specific GEOIDs. 

    columns:    list
                List of the column names to select; in the format TBLID_ORDER,
                e.g., B03002_009 for table B03002 and variable 9 (note: always 
                three digits after the _). If empty list (default), then keep 
                all columns from all requested tables.

    geos:       list
                List of the GEOIDs to select. If an empty list 
                (default), then keep all GEOIDs from all requested states.

    Returns
    -------
    Pandas hierarchical dataframe, where the first level is: estimates, moes,
    ses, replicate1, replicate2, ..., replicate80; the second level is the
    attribute columns: total pop, count Hispanic, count in poverty, etc. The
    rows are the geographic areas (e.g., tracts or counties or ...). Note that
    rows and columns follow the order of the geos and columns parameters when
    appropriate.
    """

    # sort out scale
    if scale.lower() in SUMMARY_LEVELS:
        scale_clean = SUMMARY_LEVELS[scale]
    elif str(scale) in SUMMARY_LEVELS.values():
        scale_clean = str(scale)
    else:
        raise Exception(
            "scale must a summary level code or name; see SUMMARY_LEVELS for options"
        )

    # sort out state
    # tracts and block groups require a state fips code
    if scale_clean in ["140", "150"] and state:
        state_clean = "_" + state
    else:
        state_clean = ""

    # build URLs
    fnames = []
    # loop through tables and build URL for each
    for table in tables:
        fname = (
            "https://www2.census.gov/programs-surveys/acs/replicate_estimates/"
            + str(year)
            + "/data/5-year/"
            + scale_clean
            + "/"
            + table
            + state_clean
            + ".csv.gz"
        )
        fnames.append(fname)

    # run general function to do the heavy lifting
    return get_replicate_data(fnames, columns, geos)


def get_pop(data, year):
    """
    Get the population counts associated with replicate data pulled from the
    Census website; for select years and geographic types. Works well when the
    index on data is still in the format from the Census and geographic areas
    are not being combined in func.

    Parameters
    ----------
    data:   dataframe
            Hierarchical dataframe of the type produced by get_replicate_data
            or read_replicate_file

    year:   int or str
            Ignored when zeros is False. Year of the ACS data; e.g., if 
            2011-2015, then set year to 2015

    Returns
    -------
    Dataframe of the type needed for the base parameter in replicate_ests
    function.
    """
    geo_code = data.index[0][0:3]
    if geo_code not in geo_types:
        raise Exception(
            "Built-in population data only available for:"
            + str([geo_types[i] for i in available_pop])
        )
    return zeros_data_pop(year, geo_types[geo_code])


def get_state(data):
    """
    Infers state FIPS codes from the index values in data. Works well when the
    index on data is still in the format from the Census and geographic areas 
    are not being combined in func.

    Parameters
    ----------
    data:   dataframe
            Hierarchical dataframe of the type produced by get_replicate_data
            or read_replicate_file

    Returns
    -------
    Dataframe of the type needed for the state parameter in replicate_ests
    function.
    """
    state = pd.DataFrame(data.index, index=data.index)
    state = state.GEOID.str.split("US", expand=True)
    state = state.iloc[:, 1].str[0:2].to_frame()
    state = state.rename(columns={1: "fips"})
    return state


def replicate_ests(
    func, data, rep_nans=True, zeros=False, year=None, base=None, state=None, params={}
):
    """
    Compute estimates and MOEs for an arbitrary function using ACS Variance
    Replicate Table data as inputs. The standard approach for computing the 
    MOE is robust to any functional form, except when an estimate equals zero.
    At this time only count and proportion estimates have an alternate
    formulation for the zero estimate case. 
    
    Parameters
    ----------
    func:   function
            Function that computes the estimate; func is assumed to take a
            dataframe of ACS estimates as its first term (see params parameter
            if func requires more parameters); func must return a single 
            column of estimates for multiple geographies

    data:   dataframe
            Hierarchical dataframe of the type produced by get_replicate_data
            or read_replicate_file

    rep_nans boolean
            If True (default), then replace NaN estimates with zero; if False,
            leave estimate as NaN. In either case set MOE to NaN.  
    
    zeros:  str or boolean
            Set to 'count' if func returns counts, set to 'prop' if func
            returns proportions and set to False (default) if func returns
            some other type of value. If func does not return any zeros, then
            this setting is irrelevant.

    year:   int or str
            Ignored when zeros is False. Year of the ACS data; e.g., if 
            2011-2015, then set year to 2015

    base:   single column pandas dataframe or pandas series
            Ignored when zeros is False. A population control for each row
            returned by func. Set to the denominator for each row when zeros
            is 'prop'; set to the total population for each row when zeros is
            'count'.  See get_pop function for built-in approach to get
            populations.
            
    state:  single column pandas dataframe, pandas series or str
            Ignored when zeros is False. Column of two-digit state FIPS codes
            (as strings) for each row returned by func. If all rows in data
            are in the same state, then the two-digit FIPS code (as string)
            can be used.  See get_state function for built-in approach to
            get states.

    params: dict
            Optional parameters to pass to func, where dict keys are the
            parameter names and the dict values are the parameter values.
            Assumes that a dataframe of ACS parameters is the first value 
            passed to func, and then params is passed.


    Returns
    -------
    Pandas two column dataframe, where the first column is the estimates and
    the second is the MOEs. If an MOE cannot be computed a numpy.NaN value is
    put in its place.
    """
    rep_results = apply_func(func=func, data=data, params=params)
    estimates = rep_results.pop("estimate")
    rep_diffs = rep_results.sub(estimates, axis=0) ** 2  # (rep-est)^2
    var = rep_diffs.sum(axis=1) * (4.0 / 80.0)
    se = var ** 0.5
    moe = se * 1.645
    estimates = estimates.to_frame(name="est")
    estimates["moe"] = moe
    if zeros == False:
        estimates.loc[estimates.est == 0, "moe"] = np.NaN
    elif zeros.lower() == "count" or zeros.lower() == "prop":
        estimates = _zero_correct(
            estimates,
            rep_results=rep_results,
            zeros=zeros,
            year=year,
            base=base,
            state=state,
        )
    else:
        raise Exception("zeros parameter must be set to 'count', 'prop' or False")
    estimates.loc[estimates.est.isnull(), "moe"] = np.NaN
    if rep_nans == True:
        estimates.loc[estimates.est.isnull(), "est"] = 0
    # currently not dealing with infinite estimates
    return estimates


def apply_func(func, data, params={}):
    """
    Apply and an arbitrary function to the estimates and each replicate.
    
    Parameters
    ----------
    func:   function
            Function that computes the estimate

    data:   dataframe
            Hierarchical dataframe

    params: dict
            Optional parameters to pass to func, where dict keys are the
            parameter names and the dict values are the parameter values.
            Assumes that ests is the first value passed to func, and then
            parameters is passed.

    Returns
    -------
    Pandas 81 column dataframe, where the first column is the estimates and
    the remaining columns are the replicates.
    """
    estimates = func(data.ESTIMATE, **params)
    # subset just the replicates
    replicates = data.drop(["ESTIMATE", "MOE", "SE"], axis=1, level=0)
    # clean out unused column names
    replicates.columns = replicates.columns.remove_unused_levels()
    # apply the user function to each replicate
    # NOTE: This is probably the slowest possible way of doing this. This
    #       approach was chosen to allow arbitrary parameters to be passed to
    #       the user's function. Previous versions in the repo used some
    #       groupby and multiprocessing tricks, but could not get them working
    #       with extra parameters. Consider refactoring for speed in the future.
    rep_results = [
        func(data[replicate], **params) for replicate in replicates.columns.levels[0]
    ]
    rep_results = pd.concat(rep_results, axis=1, keys=replicates.columns.levels[0])
    # cleanup
    rep_results["ESTIMATE"] = estimates
    rep_results = rep_results.replace([np.inf, -np.inf], 0)  # per census documentation
    return rep_results


def insert_column(data, column, name):
    """
    Insert a column into replicates dataframe. The same column will go into
    estimates and replicates; the corresponding MOE and standard error columns
    (if available) will be set to zero.

    Parameters
    ----------
    data:   dataframe
            Hierarchical dataframe

    column: pandas series
            Column of data to be added. Assumes the indexes are GEOIDs
            that match the indexes in the data dataframe.

    name:   str
            Name to assign to column.

    Returns
    -------
    New dataframe with column inserted. Note that the source dataframe is not
    altered and the inserted columns are copies of source column.
    """
    data = data.copy()
    for col in data.columns.levels[0]:
        # using a for loop to ensure that each new column is independent from
        # the source data and each of the inserted columns; there may be a
        # better/faster approach
        data[col, name] = column.copy()
    if "moe" in data.columns.levels[0]:
        data["moe", name] = 0
    if "SE" in data.columns.levels[0]:
        data["SE", name] = 0
    data = data.sort_index(axis=1)
    return data


############################################################
### Internal functions to compute MOEs on zero estimates ###
############################################################

# Geography types in the replicate data
geo_types = {
    "010": "us",
    "040": "state",
    "050": "county",
    "060": "cnysub",
    "140": "tract",
    "150": "blkgrp",
    "160": "place",
    "250": "amindland",
    "310": "msa",
    "500": "congress",
    "860": "zcta",
}

# Same k-values for 2014 and 2015.
def _get_k(row, pop_col):
    if row[pop_col] <= 4999:
        return 4
    if row[pop_col] <= 9999:
        return 8
    if row[pop_col] <= 19999:
        return 10
    if row[pop_col] <= 29999:
        return 14
    if row[pop_col] <= 49999:
        return 18
    if row[pop_col] >= 50000:
        return 22
    raise Exception("not a legitimate population value:" + str(row.iloc[0]))


# Only read the support population CSV the first time it's needed
_zeros_data_pop = {}


def zeros_data_pop(year, geo_type):
    pop_data = pd.read_csv(
        "support_data/pop_" + str(year) + "_" + geo_type + ".csv", index_col="GEOID"
    )
    _zeros_data_pop[(year, geo_type)] = pop_data
    return _zeros_data_pop[(year, geo_type)]


# Only read the support weights CSV the first time it's needed; note that
# the state weight read in here is applied to all subgeographies
_zeros_data_weight = {}


def zeros_data_weight(year):
    if year not in _zeros_data_weight:
        weight_data = pd.read_csv(
            "support_data/average_weights_" + str(year)[2:] + ".csv",
            dtype={"fips": str},
        )
        weight_data = weight_data.set_index("fips")
        _zeros_data_weight[year] = weight_data
    return _zeros_data_weight[year]


# The heavy lifting to compute MOEs on zero estimates
def _zero_correct(estimates, rep_results, zeros, year, base, state):
    if zeros == "count":  # need to correct zero estimates
        # identify rows with zero est or rows with no variation in replicate values
        condition = (estimates.est == 0.0) | (rep_results.nunique(axis=1) == 1)
        zero_ests = pd.DataFrame(index=estimates.index[condition])
    elif zeros == "prop":  # 0% and 100% estimates need to be corrected
        zero_ests = pd.DataFrame(
            index=estimates.index[(estimates.est == 0.0) | (estimates.est == 1.0)]
        )
    else:
        raise Exception("zeros parameter must be set to 'count', 'prop' or False")

    if zero_ests.shape[0] == 0:  # no zero estimates so don't continue
        return estimates

    # Test if base and state length match estimates length
    if base.shape[0] != estimates.shape[0]:
        raise Exception(
            "length of base ({}) does not match length of estimates ({})".format(
                base.shape[0], estimates.shape[0]
            )
        )
    if not isinstance(state, str):
        if state.shape[0] != estimates.shape[0]:
            raise Exception(
                "length of state ({}) does not match length of estimates ({})".format(
                    state.shape[0], estimates.shape[0]
                )
            )

    # Combine all the parts needed to compute MOEs
    weights = zeros_data_weight(year)
    if isinstance(base, pd.Series):  # allow user to pass Series or DataFrame
        base = base.to_frame()
    zero_ests = zero_ests.merge(base, how="left", left_index=True, right_index=True)
    if isinstance(state, str):  # allow user to pass one FIPS code for all data
        state = pd.DataFrame(state, index=estimates.index, columns=["fips"])
    elif isinstance(state, pd.Series):  # allow user to pass Series or DataFrame
        state = state.to_frame()
    state = state.merge(weights, how="left", left_on=state.columns[0], right_index=True)
    zero_ests = zero_ests.merge(state, how="left", left_index=True, right_index=True)

    # Get the MOEs
    if zeros == "count":
        zero_ests["k_val"] = zero_ests.apply(
            _get_k, axis=1, pop_col=str(base.columns[0])
        )
        zero_ests["moe"] = 1.645 * np.sqrt(zero_ests.avg_weight * zero_ests.k_val)
    else:
        zero_ests["pop_weight"] = zero_ests.avg_weight / (
            zero_ests[base.columns[0]] * 1.0
        )
        zero_ests["p_star"] = 2.3 * zero_ests.pop_weight
        zero_ests.loc[zero_ests.p_star > 0.5, "p_star"] = 0.5
        zero_ests["moe"] = 1.645 * np.sqrt(
            zero_ests.p_star * (1 - zero_ests.p_star) * zero_ests.pop_weight
        )

    # Merge MOEs back into the estimates file
    estimates.loc[zero_ests.index, "moe"] = zero_ests.moe
    return estimates


############################################################


if __name__ == "__main__":

    import traceback

    data_path = "../data/"

    # test simple table reader
    data = read_replicate_file(data_path + "B03002.csv")
    data = read_replicate_file(data_path + "B03002.csv.gz")
    data = read_replicate_file(
        "https://www2.census.gov/programs-surveys/acs/replicate_estimates/2015/data/5-year/040/B03002.csv.gz"
    )

    # API downloader
    data = get_replicate_data_api(["B03002"], 2015, "010")
    data = get_replicate_data_api(["B03002"], 2015, "us")
    # data = get_replicate_data_api(['B03002'], 2015, '040')
    # data = get_replicate_data_api(['B03002'], 2015, '050')
    # data = get_replicate_data_api(['B03002'], 2015, '060')
    data = get_replicate_data_api(["B03002"], 2015, "140", "16")
    # data = get_replicate_data_api(['B03002'], 2015, '150', '16')
    # data = get_replicate_data_api(['B03002'], 2015, '160')
    # data = get_replicate_data_api(['B03002'], 2015, '250')
    # data = get_replicate_data_api(['B03002'], 2015, '310')
    # data = get_replicate_data_api(['B03002'], 2015, '500')
    # data = get_replicate_data_api(['B03002'], 2015, '860')
    data = get_replicate_data_api(["B03001", "B03002"], 2015, "040")
    data = get_replicate_data_api(["B03001", "B03002"], 2015, "140", "16")
    # data = get_replicate_data_api(['B03003','B03002'], 2015, '150', '16')

    # test some columns and some GEOIDs
    ## tracts (include bad columns and GEOIDs)
    data = get_replicate_data(
        [data_path + "B03002_16.csv", data_path + "B03002_11.csv"],
        ["B03002_006", "B05001_003", "B03002_005"],
        [
            "04000US54",
            "04000US04",
            "04000US15",
            "14000US16001001201",
            "14000US16001010321",
        ],
    )
    ## states (include bad columns and GEOIDs)
    data = get_replicate_data(
        [data_path + "B03001.csv", data_path + "B03002.csv"],
        ["B03002_006", "B05001_003", "B03002_005"],
        [
            "04000US54",
            "04000US04",
            "04000US15",
            "14000US16001001201",
            "14000US16001010321",
        ],
    )
    # test all columns and some GEOIDs
    data = get_replicate_data(
        [data_path + "B03001.csv", data_path + "B03002.csv", data_path + "B05001.csv"],
        geos=["04000US54", "04000US04", "04000US15"],
    )
    # test some columns and all GEOIDs
    data = get_replicate_data(
        [data_path + "B03001.csv", data_path + "B03002.csv", data_path + "B05001.csv"],
        ["B03001_001", "B05001_003", "B03002_006", "B03002_005"],
    )
    # test all columns and all GEOIDs
    data = get_replicate_data(
        [data_path + "B03001.csv", data_path + "B03002.csv", data_path + "B05001.csv"]
    )

    import multi_variable_measures as mvm

    # test ests and moes
    data = get_replicate_data(
        [data_path + "B01001.csv"],
        ["B01001_003", "B01001_004", "B01001_005"],
        ["05000US01001", "05000US01005", "05000US01017", "05000US01035"],
    )
    results = replicate_ests(mvm.get_sum, data, zeros=False)

    # test zeros estimates: counts
    data = get_replicate_data([data_path + "B01001.csv"], ["B01001_025", "B01001_049"])
    population = get_pop(data, 2015)
    state = get_state(data)
    results = replicate_ests(
        mvm.get_sum, data, zeros="count", year=2015, base=population, state=state
    )

    # test zeros estimates: proportions
    data = get_replicate_data([data_path + "B01001.csv"], ["B01001_025", "B01001_001"])
    state = get_state(data)
    results = replicate_ests(
        mvm.get_div,
        data,
        zeros="prop",
        year=2015,
        base=data.estimate.B01001_001,
        state=state,
    )

    # test zeros estimates: state string
    data = get_replicate_data(
        [data_path + "B03002_11.csv"], ["B03002_019", "B03002_001"]
    )
    state = get_state(data)
    results = replicate_ests(mvm.get_div, data, zeros=False)
    results = replicate_ests(
        mvm.get_div,
        data,
        zeros="prop",
        year=2015,
        base=data.estimate.B03002_001,
        state="11",
    )

    # test row collapsing
    def get_sum_agg(ests):
        return ests.groupby(ests.index, axis=0).sum()

    data = get_replicate_data([data_path + "B02015.csv"], ["B02015_004", "B02015_023"])
    state = get_state(data)  # state codes for each county
    population = get_pop(data, 2015)  # population for each county
    population.index = state.iloc[:, 0]  # set index to state codes
    agg_pop = get_sum_agg(population)  # population to match output of get_sum_agg()
    agg_data = data.copy()  # work on a copy of data
    agg_data.index = state.iloc[:, 0]  # set index to state codes
    agg_state = pd.DataFrame(
        index=agg_pop.index
    )  # state codes to match output of get_sum_agg()
    agg_state["codes"] = agg_state.index  # state codes
    agg_results = pd.DataFrame()
    for v in data.columns.levels[1]:
        results = replicate_ests(
            get_sum_agg,
            agg_data.loc[:, (slice(None), v)],
            zeros="count",
            year=2015,
            base=agg_pop,
            state=agg_state,
        )
        results.columns = [v + i for i in ["_est", "_moe"]]
        agg_results = pd.concat([agg_results, results], axis=1)

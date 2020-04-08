"""
Script to compute ACS margins of error using a Monte Carlo type simulation
approach. If say three input values are needed to compute some final composite
estimate, then each of the input values is drawn from its own normal
distribution and those values combined into the estimate; this process is
repeated multiple times to get an empirical distribution of the combined
estimates. The MOE is then computed off of this empirical distribution. 

This script it is only tested to work under the conditions needed for the
paper. More flexibility and error handling should be added if put into general
use.
"""


import pandas as pd
import numpy as np
from scipy.stats import norm as NORM


# cenpy.moe.pseudo(sum, estim, moe)
def pseudo(
    func,
    ests,
    moes,
    sims=100,
    ignore_zeros="all",
    base=None,
    truncate=False,
    whole=False,
    analytic=True,
    rep_style=True,
    single_draw=False,
    replace_na=None,
    seed=None,
    params={},
):
    """
    Compute estimates and MOEs for an arbitrary function using a simulation
    approach based on draws from a distribution around each input estimate.
    The standard approach for computing the MOE is robust to any functional
    form.  Due to the high MOEs on input estimates that equal zero, the
    default option is to ignore these MOEs since they greatly widen the
    sampling distribution; also they are often associated with non-residential
    areas so zero MOE in these cases is a reasonable assumption. 

    Parameters
    ----------
    func:   function
            Function that computes the estimate; func must return a single
            column of estimates for multiple geographies

    ests:   pandas dataframe
            nxm dataframe with n observations on m variables from the ACS. 
            Assumed that passing ests to func will give valid results.

    moes:   pandas dataframe
            nxm dataframe of MOEs aligned with ests.

    sims:   int
            The number of simulations to run when computing the pseudo-MOE.

    ignore_zeros: string
            If 'all', then set MOEs on all zero estimates to zero (default).
            If 'partial', then set MOEs on zero population geographies to
            zero. If 'no', then use the published MOEs.

    base:   single column pandas dataframe or pandas series
            Ignored when ignore_zeros is False. A population control for each
            row returned by func. Set to the total population for each row
            when zeros is 'count'.  See get_pop function
            (replicate_table_utils.py) for built-in approach to get
            populations.

    truncate: boolean
            If True, then replace negative simulated estimates with zero. If
            False, then do not adjust random draws (default).

    whole:  boolean
            If True, then round the simulated estimates to whole numbers to
            reflect whole people, households or housing units. If False, allow
            fractional values (default).

    analytic: boolean
            If True, compute MOEs based on the variance of all simulated
            values (default). If False, compute MOEs as half the confidence 
            interval (CI), where the CI is defined as the range after removing 
            the lowest 5% of simulated values and highest 5%. NOTE: If
            analytic is False, then rep_style must also be False.

    rep_style: boolean
            If True, use the equations from Brault (2014) that follows the
            replicate variance formulas. If False, do not make replicate style
            adjustments.

    single_draw: boolean
            If True, then make one draw off of a standard normal distribution
            and assign all input values based on their individual normal
            distribution at this point. If False, then each input value is an
            independent draw off of its own normal distribution (default).

    replace_na: int, float, None
            If int or float, then replace non-finite simulated estimates with
            that int or float. Non-finite simulated estimates can arise in
            many cases, e.g., when a randomly drawn denominator is zero. The
            presence of non-finite simulated estimates may be affected by the
            settings of truncate and whole. If one or more simulated estimates
            are non-finite, the final variance and MOE will be NA. If None, do
            nothing (default).

    seed:   int or None
            Seed passed to np.random.seed() before simulating values. If None
            (default), then each run will be different. Each run will be the
            same for any particular int passed.

    params: dict
            Optional parameters to pass to func, where dict keys are the
            parameter names and the dict values are the parameter values.
            Assumes that ests is the first value passed to func, and then
            parameters are passed.

    Returns
    -------

    results : dataframe
              Dataframe where the first column is the result of func and the second
              is the MOE on those values.

    """
    # result using the raw ACS data
    result = func(ests, **params)

    # The SEs come from the replicate approach, so we will mirror that here.
    # Divide the variance (SE^2) of each input variable by 4 and use that for
    # the simulations. Then when computing the final variance on the result,
    # multiply the 4 back in. That equation matches the replicate variance
    # equation that has 4/80, but in this case is 4/sims. Based in part on
    # Brault (2014).
    std_errs = moes / 1.645
    if rep_style is True:
        errs = np.sqrt((std_errs ** 2) * ((1 - 0.5) ** 2))
    elif rep_style is False:
        errs = np.sqrt(std_errs ** 2)

    # data prep to compute simulated ACS estimates
    zero_errs = errs == 0  # identify values with an MOE of zero
    zero_in_cols = [
        zero_errs[column].any() for column in zero_errs
    ]  # check each column, identify if there is at least one True
    errs[zero_errs] = 999  # reset zero errs so the np.random.normal doesn't fail

    # setup zeros cleaning
    zero_ests = False
    if ignore_zeros == "all":
        zero_ests = ests == 0  # identify all values with an estimate of zero
    elif ignore_zeros == "partial":
        # create boolean dataframe of shape ests where all columns identify empty geographies
        if base is None:
            raise Exception(
                "base must be a pandas series or dataframe when ignore_zeros=='partial'"
            )
        if isinstance(base, pd.Series):  # allow user to pass Series or DataFrame
            base = base.to_frame()
        base = base.copy()
        base["zero_bool"] = base.iloc[:, 0] == 0
        zero_ests = ests.copy()
        for col in zero_ests.columns:
            zero_ests[col] = base.zero_bool
    elif ignore_zeros is not "no":  # to catch bad parameter values
        raise Exception("ignore_zeros must be 'all', 'partial' or 'no'")

    # setup output array
    sim_results = np.zeros(
        (result.shape[0], sims)
    )  # assumes func returns an (n x none) or (n x 1)

    # run the function sim times and store the results
    np.random.seed(seed)  # if seed not None, then we get the same output every time
    for sim in range(sims):
        if single_draw is True:
            sim_ests = ests.values + (errs.values * np.random.standard_normal())
        elif single_draw is False:
            sim_ests = np.random.normal(ests.values, errs.values)
        else:  # to catch bad parameter values
            raise Exception("single_draw must be boolean")

        sim_ests = pd.DataFrame(sim_ests, index=ests.index, columns=ests.columns)

        if True in zero_in_cols:  # only want to mask if there is at least one zero
            sim_ests[zero_errs] = ests[
                zero_errs
            ]  # this just says that ests without error should be the est

        if zero_ests is not False:
            sim_ests[
                zero_ests
            ] = 0  # this says that zero ests should have no error (big assumption)

        if truncate is True:
            sim_ests[sim_ests < 0] = 0  # this forces negative simulated ests to zero
        elif truncate is not False:  # to catch bad parameter values
            raise Exception("truncate must be boolean")

        if whole is True:
            sim_ests = sim_ests.round(0)  # this forces all estimates to whole numbers
        elif whole is not False:  # to catch bad parameter values
            raise Exception("whole must be boolean")

        # run the function... finally
        sim_result = func(sim_ests, **params)

        if isinstance(replace_na, (int, float)) and not isinstance(replace_na, bool):
            sim_result[
                np.invert(np.isfinite(sim_result))
            ] = replace_na  # replace non-finite values
        elif replace_na is not None:
            raise Exception("replace_na must be int, float or None")

        sim_results[:, sim] = sim_result

    result = np.expand_dims(result, 1)  # make nx1
    if analytic is True:
        # compute pseudo standard errors based on the variance of the simulated estimates
        if rep_style is True:
            pseudo_var = (4.0 / sims) * ((sim_results - result) ** 2).sum(
                axis=1
            )  # ACS specific; based on correspondence with Brault
            pseudo_se = np.sqrt(pseudo_var)
        elif rep_style is False:
            pseudo_se = sim_results.std()  # textbook equation
        pseudo_se = pd.Series(pseudo_se, index=ests.index)

        # compute pseudo MOEs from the pseudo standard errors
        alpha = 1 - 0.90  # 1 - confidence level
        phi = 1 - (alpha / 2.0)
        cdfi = NORM.ppf(phi)
        pseudo_moe = pseudo_se * cdfi
    elif analytic is False:
        if rep_style is True:
            raise Exception("If analytic is False, rep_style must also be False")
        # compute pseudo MOEs as half the range of the 90% confidence interval on the simulated estimates
        lower = np.percentile(sim_results, 5, interpolation="lower", axis=1)
        upper = np.percentile(sim_results, 95, interpolation="higher", axis=1)
        pseudo_moe = pd.Series((upper - lower) / 2.0, index=ests.index)
    estimates = pd.DataFrame({"est": np.squeeze(result), "moe": pseudo_moe})
    return estimates


############################################################


if __name__ == "__main__":

    import multi_variable_measures as mvm
    import replicate_table_utils as rtu

    data_path = "../data/"

    #### TEST DIVIDE ####
    # get data
    data = rtu.get_replicate_data(
        [data_path + "B15002_050_yr15.csv"], columns=["B15002_011", "B15002_002"]
    )
    population = rtu.get_pop(data, 2015)
    # default settings
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe)
    # print(results.head())
    # mess with the zeros setting (turn off)
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe, ignore_zeros="no")
    # print(results.head())
    # mess with the zeros setting (just real zeros)
    results = pseudo_ests(
        mvm.get_div, data.estimate, data.moe, ignore_zeros="partial", base=population
    )
    # print(results.head())
    # mess with the sampling setting
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe, single_draw=True)
    # print(results.head())
    # mess with both settings
    results = pseudo_ests(
        mvm.get_div, data.estimate, data.moe, ignore_zeros="no", single_draw=True
    )
    # print(results.head())
    # mess with seed
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe, seed=1234)
    # mess with truncate
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe, truncate=True)
    # mess with whole
    results = pseudo_ests(mvm.get_div, data.estimate, data.moe, whole=True)
    # mess with analytic
    results = pseudo_ests(
        mvm.get_div, data.estimate, data.moe, analytic=False, rep_style=False
    )
    # published data
    pubs = pd.read_csv(
        data_path + "acs_S1501_050_yr15.csv", usecols=["HC04_EST_VC11", "HC04_MOE_VC11"]
    )
    # print(pubs.head() / 100.0)

    #### TEST SUM ####
    # get data
    data = rtu.get_replicate_data(
        [data_path + "B01001_050_yr15.csv"],
        columns=["B01001_003", "B01001_004", "B01001_005", "B01001_006"],
    )
    population = rtu.get_pop(data, 2015)
    # default settings
    results = pseudo_ests(mvm.get_sum, data.estimate, data.moe)
    # print(results.head(10))
    # mess with the zeros setting (turn off)
    results = pseudo_ests(mvm.get_sum, data.estimate, data.moe, ignore_zeros="no")
    # print(results.head(10))
    # mess with the zeros setting (only true zeros)
    results = pseudo_ests(
        mvm.get_sum, data.estimate, data.moe, ignore_zeros="partial", base=population
    )
    # print(results.head(10))
    # mess with the sampling setting
    results = pseudo_ests(mvm.get_sum, data.estimate, data.moe, single_draw=True)
    # print(results.head(10))
    # mess with both settings
    results = pseudo_ests(
        mvm.get_sum, data.estimate, data.moe, ignore_zeros="no", single_draw=True
    )
    # print(results.head(10))
    # mess with seed
    results = pseudo_ests(mvm.get_sum, data.estimate, data.moe, sims=1000, seed=1234)
    print(results.head(10))
    # mess with truncate
    results = pseudo_ests(
        mvm.get_sum,
        data.estimate,
        data.moe,
        truncate=True,
        ignore_zeros="no",
        seed=1234,
    )
    # print(results.head(10))
    # mess with whole
    results = pseudo_ests(mvm.get_sum, data.estimate, data.moe, whole=True, seed=1234)
    # print(results.head(10))
    # mess with analytic
    results = pseudo_ests(
        mvm.get_sum,
        data.estimate,
        data.moe,
        sims=1000,
        analytic=False,
        rep_style=False,
        seed=1234,
    )
    print(results.head(10))
    # mess with rep_style
    results = pseudo_ests(
        mvm.get_sum, data.estimate, data.moe, sims=1000, rep_style=False, seed=1234
    )
    # print(results.head(10))
    # published data
    pubs = pd.read_csv(
        data_path + "acs_B05003_050_yr15.csv", usecols=["HD01_VD03", "HD02_VD03"]
    )
    # print(pubs.head(10))

    #### TEST UNIVARIATE ####
    # get data
    data = rtu.get_replicate_data(
        [data_path + "B01001_050_yr15.csv"], columns=["B01001_003"]
    )
    population = rtu.get_pop(data, 2015)
    # default settings
    results = pseudo_ests(mvm.univariate_test, data.estimate, data.moe)
    # print(results.head())
    # mess with the zeros setting (turn off)
    results = pseudo_ests(
        mvm.univariate_test, data.estimate, data.moe, ignore_zeros="no"
    )
    # print(results.head())
    # mess with the zeros setting (only true zeros)
    results = pseudo_ests(
        mvm.univariate_test,
        data.estimate,
        data.moe,
        ignore_zeros="partial",
        base=population,
    )
    # print(results.head())
    # mess with the sampling setting
    results = pseudo_ests(
        mvm.univariate_test, data.estimate, data.moe, single_draw=True
    )
    # print(results.head())
    # mess with both settings
    results = pseudo_ests(
        mvm.univariate_test,
        data.estimate,
        data.moe,
        ignore_zeros="no",
        single_draw=True,
    )
    # print(results.head())
    # jack up the number simulations
    results = pseudo_ests(mvm.univariate_test, data.estimate, data.moe, sims=1000)
    # print(results.head())
    # mess with seed
    results = pseudo_ests(mvm.univariate_test, data.estimate, data.moe, seed=1234)
    # mess with truncate
    results = pseudo_ests(mvm.univariate_test, data.estimate, data.moe, truncate=True)
    # mess with whole
    results = pseudo_ests(mvm.univariate_test, data.estimate, data.moe, whole=True)
    # mess with analytic
    results = pseudo_ests(
        mvm.univariate_test, data.estimate, data.moe, analytic=True, rep_style=False
    )
    # published data
    pubs = pd.concat([data.estimate, data.moe], axis=1)
    # print(pubs.head())

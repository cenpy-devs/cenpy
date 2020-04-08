"""
Tools to compute estimates and analytic MOEs using published ACS estimates and
MOEs. Following the equations in Appendix 3 of the Census Bureau's ACS guide,
"A Compass for Understanding and Using American Community Survey Data: What 
Researchers Need to Know"
https://www.census.gov/content/dam/Census/library/publications/2009/acs/ACSResearch.pdf
"""

import pandas as pd
import numpy as np
import warnings


def fxn():
    # suppress the sqrt warning since we correct it later
    warnings.warn("invalid value encountered in sqrt", RuntimeWarning)


# cenpy.moe.analytic_sum(ests, moes)
def analytic_sum(ests, moes):
    """
    Compute estimates and MOEs for summed variables using ACS analytic method
    for MOE computation. Requires published ACS estimates and MOEs for the input
    variables.
    https://www.census.gov/content/dam/Census/library/publications/2009/acs/ACSResearch.pdf

    Parameters
    ----------
    ests:   dataframe
            n x m dataframe of ACS estimates of the variables to be summed,
            where n is the number of geographies and m the number of variables
            to be summed.

    moes:   dataframe
            n x m dataframe of ACS MOEs aligned to match ests.

    Returns
    -------
    Pandas two column dataframe, where the first column is the estimates and
    the second is the MOEs.
    """
    ests_comp = ests.sum(axis=1)
    moes = moes.copy()
    # if multiple zero estimates, just use the max MOE in the MOE computation
    zeros = moes[ests == 0].max(axis=1)
    moes[ests == 0] = 0  # zero out MOE on all zero estimates
    moes["zero"] = zeros  # new column with max MOE on zero ests
    moes_comp = np.sqrt((moes ** 2).sum(axis=1))
    ests_comp = ests_comp.to_frame(name="est")
    ests_comp["moe"] = moes_comp
    return ests_comp


def _analytic_div(ests_comp, ests, moes):
    """
    The ratio MOE division equation is used in both the ratio and proportion
    computations.
    """
    return (
        np.sqrt(moes.iloc[:, 0] ** 2 + (ests_comp ** 2 * moes.iloc[:, 1] ** 2))
        / ests.iloc[:, 1]
    )


def analytic_ratio(ests, moes):
    """
    Compute estimates and MOEs for the ratio of two variables using ACS
    analytic method for MOE computation. Note: the numerator of a ratio is not
    a subset of the denominator (see analytic_prop). Requires published ACS
    estimates and MOEs for the input variables.
    https://www.census.gov/content/dam/Census/library/publications/2009/acs/ACSResearch.pdf

    Parameters
    ----------
    ests:   dataframe
            n x 2 dataframe of ACS estimates, where the first column contains
            the numerators and the second contains the denominators; n is the
            number of geographies.

    moes:   dataframe
            n x 2 dataframe of ACS MOEs aligned to match ests.

    Returns
    -------
    Pandas two column dataframe, where the first column is the estimates and
    the second is the MOEs.
    """
    ests_comp = ests.iloc[:,0] / (ests.iloc[:,1]*1.0)
    moes_comp = _analytic_div(ests_comp, ests, moes)
    ests_comp = ests_comp.to_frame(name="est")
    ests_comp["moe"] = moes_comp
    return ests_comp


def analytic_prop(ests, moes):
    """
    Compute estimates and MOEs for the proportion between two variables using ACS
    analytic method for MOE computation. Note: the numerator of a proportion is
    a subset of the denominator (see analytic_ratio). Requires published ACS
    estimates and MOEs for the input variables.
    https://www.census.gov/content/dam/Census/library/publications/2009/acs/ACSResearch.pdf

    Parameters
    ----------
    ests:   dataframe
            n x 2 dataframe of ACS estimates, where the first column contains
            the numerators and the second contains the denominators; n is the
            number of geographies.

    moes:   dataframe
            n x 2 dataframe of ACS MOEs aligned to match ests.

    Returns
    -------
    Pandas two column dataframe, where the first column is the estimates and
    the second is the MOEs.
    """
    ests_comp = ests.iloc[:,0] / (ests.iloc[:,1]*1.0)
    with warnings.catch_warnings():
        # there might be a negative in the sqrt, suppress the warning
        warnings.simplefilter("ignore")
        fxn()
        moes_comp = (
            np.sqrt(moes.iloc[:, 0] ** 2 - (ests_comp ** 2 * moes.iloc[:, 1] ** 2))
            / ests.iloc[:, 1]
        )

    moes_pos = _analytic_div(ests_comp, ests, moes)
    # replace the negative sqrt cases with positive sqrt (cannot sqrt a negative)
    moes_comp[moes_comp.isnull()] = moes_pos[moes_comp.isnull()]
    # replace zero MOEs with the ratio equation (this appears to only happen
    #        when the ratio=1 since the MOEs on the inputs will be the same
    #        making the numerator=0)
    moes_comp[moes_comp == 0] = moes_pos[moes_comp == 0]

    ests_comp = ests_comp.to_frame(name="est")
    ests_comp["moe"] = moes_comp
    return ests_comp


if __name__ == "__main__":

    np.random.seed(123)
    ests = pd.DataFrame(np.random.randint(1, 100, (5, 4)))
    ests.iloc[0, 1] = 0
    ests.iloc[1, 0] = 0
    ests.iloc[3, 2] = 0
    ests.iloc[3, 3] = 0
    ests.iloc[2, 1] = 99
    moes = pd.DataFrame(np.random.randint(1, 100, (5, 4)))
    results_sum = analytic_sum(ests, moes)
    ests2 = ests.iloc[:, [0, 1]]
    moes2 = moes.iloc[:, [0, 1]]
    results_ratio = analytic_ratio(ests2, moes2)
    results_prop = analytic_prop(ests2, moes2)

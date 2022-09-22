import pandas
import numpy
from fuzzywuzzy import fuzz


def _fuzzy_match(matchtarget, matchlist, return_table=False):
    """
    Conduct a fuzzy match with matchtarget, within the list of possible match candidates in matchlist. 

    Parameters
    ---------
    matchtarget :   str
                 a string to be matched to a set of possible candidates
    matchlist   :   list of str
                 a list (or iterable) containing strings we are interested in matching
    return_table:   bool
                 whether to return the full table of scored candidates, or to return only the single
                 best match. If False (the default), only the best match is returned.
    
    Notes
    -----
    consult the docstring for Product.check_match for more information on how the actual matching
    algorithm works. 
    """
    split = matchtarget.split(",")
    if len(split) == 2:
        target, state = split
    elif len(split) == 1:
        target = split[0]
    else:
        raise AssertionError(
            "Uncertain place identifier {}. The place identifier should "
            'look something like "placename, state" or, for larger areas, '
            "like Combined Statistical Areas or Metropolitan Statistical Areas,"
            "placename1-placename2, state1-state2-state3".format(target)
        )

    table = pandas.DataFrame({"target": matchlist})
    table["score"] = table.target.apply(
        lambda x: fuzz.partial_ratio(target.strip().lower(), x.lower())
    )
    if len(split) == 1:
        if (table.score == table.score.max()).sum() > 1:
            ixmax, rowmax = _break_ties(matchtarget, table)
        else:
            ixmax = table.score.idxmax()
            rowmax = table.loc[ixmax]
        if return_table:
            return rowmax, table.sort_values("score")
        return rowmax

    in_state = table.target.str.lower().str.endswith(state.strip().lower())

    assert any(in_state), (
        "State {} is not found from place {}. "
        "Should be a standard Census abbreviation, like"
        " CA, AZ, NC, or PR".format(state, matchtarget)
    )
    table = table[in_state]
    if (table.score == table.score.max()).sum() > 1:
        ixmax, rowmax = _break_ties(matchtarget, table)
    else:
        ixmax = table.score.idxmax()
        rowmax = table.loc[ixmax]
    if return_table:
        return rowmax, table.sort_values("score")
    return rowmax


def _coerce(data, cast_to = numpy.float64):
    """
    Convert each column of data to cast_to. If a conversion of a column fails, move onto
    the next column.

    Parameters
    ----------
    data    :   DataFrame or Series

    cast_to :   type, default numpy.float64
             One of: numpy.int8, numpy.float64, str, int, etc..

    Returns
    -------
    data with columns casted to specified type
    """
    if isinstance(data, pandas.DataFrame):
        data = data.copy() # Don't operate on user's data
        for column in data.columns:
            data[column] = _coerce(data[column], cast_to = cast_to)
        return data
    elif isinstance(data, pandas.Series):
        try:
            return data.astype(cast_to)
        except:
            return data
    else:
        raise TypeError("_coerce is designed to only work"
                        "with pandas DataFrames and Series")


def _replace_missing(data):

    """
    Replace ACS missing values using numpy.nan. 

    Parameters
    ----------
    data     :   DataFrame or Series 

    Returns
    -------
    data with missing values changed to numpy.nans
    """

    acs_missing = [-999999999, -888888888, -666666666,
                   -555555555, -333333333, -222222222]

    if isinstance(data, pandas.DataFrame):
        data = data.copy()
        for column in data.columns:
            data[column] = _replace_missing(data[column])
        return data
    elif isinstance(data, pandas.Series):
        return data.replace(acs_missing, numpy.nan)
    else:
        raise TypeError("_replace_missing is designed to only work"
                        "with pandas DataFrames and Series")


def _break_ties(matchtarget, table):
    """
    break ties in the fuzzy matching algorithm using a second scoring method 
    which prioritizes full string matches over substring matches.  
    """
    split = matchtarget.split(",")
    if len(split) == 2:
        target, state = split
    else:
        target = split[0]
    table["score2"] = table.target.apply(
        lambda x: fuzz.ratio(target.strip().lower(), x.lower())
    )
    among_winners = table[table.score == table.score.max()]
    double_winners = among_winners[among_winners.score2 == among_winners.score2.max()]
    if double_winners.shape[0] > 1:
        ixmax = double_winners.score2.idxmax()
        ixmax_row = double_winners.loc[ixmax]
        warn(
            "Cannot disambiguate placename {}. Picking the shortest, best "
            "matched placename, {}, from {}".format(
                matchtarget, ixmax_row.target, ", ".join(double_winners.target.tolist())
            )
        )
        return ixmax, ixmax_row
    ixmax = double_winners.score2.idxmax()
    return ixmax, double_winners.loc[ixmax]


def _can_int(char):
    """check if a character can be turned into an integer"""
    try:
        int(char)
        return True
    except ValueError:
        return False

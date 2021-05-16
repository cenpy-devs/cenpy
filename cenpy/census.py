import numpy as np
import pandas as pd

from .utils import RestApiBase, lazy_property, chunks


class CensusDataset(RestApiBase):
    def __init__(self, url, key=None, session=None):
        self.url = url
        self.key = key
        super(CensusDataset, self).__init__(session=session)

    @lazy_property
    def variables(self):
        response = self._get(f"{self.url}/variables.json")
        response.raise_for_status()
        df = pd.DataFrame.from_dict(response.json()["variables"]).T
        df.predicateType = df.predicateType.replace(["string", np.nan], "str")
        return df

    @lazy_property
    def geographies(self):
        response = self._get(f"{self.url}/geography.json")
        return pd.DataFrame(response.json()["fips"])

    def query(
        self,
        get : list ,
        for_dict : dict,
        in_dict : dict = {},
        key : str = '',
        ):

        result = None

        # census api caps each query to 50 get variables
        for c in chunks(sorted(get), 50):

            params = {
                "get": ",".join(c),
                "for": "+".join([f"{k}:{v}" for k, v in for_dict.items()]),
            }

            if in_dict:
                # convert lists to csv
                params_in_dict = {}
                params_in_dict.update(in_dict)
                params_in_dict.update(
                    {k: ",".join(v) for k, v in in_dict.items() if isinstance(v, list)}
                )

                params["in"] = "+".join([f"{k}:{v}" for k, v in params_in_dict.items()])

            if key or self.key:
                params["key"] = key if key else self.key

            response = self._get(self.url, params=params)
            response.raise_for_status()

            # convert to DataFrame
            chunk_result = pd.DataFrame.from_records(
                response.json()[1:],
                columns=response.json()[0],
            )

            # replace placeholder values
            chunk_result.replace(
                to_replace=r"\-\d{9}",
                value=np.nan,
                regex=True,
                inplace=True,
            )

            # convert each variable to type provided in /variables.json
            type_dict = {
                k: eval(self.variables.loc[k, "predicateType"])
                for k in chunk_result.columns
                if k not in list(self.geographies.name)
            }
            chunk_result = chunk_result.astype(type_dict, errors="ignore")

            # pull out geographies in columns - for merge and reorganize
            geographies = [
                i for i in chunk_result.columns if i in list(self.geographies.name)
            ]

            # combine results if multiple queries were necessary
            if isinstance(result, pd.DataFrame):

                # merge on geographies
                result = pd.merge(result, chunk_result, on=geographies)

            else:
                result = chunk_result

            # (optional) reorganize columns - move geographies first
            result = result[
                geographies + [i for i in result.columns if i not in geographies]
            ]

        return result

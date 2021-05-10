
import numpy as np
import pandas as pd

from cenpy.utils import RestApiBase, lazy_property, chunks


class CensusCatalog(RestApiBase):

    url = 'https://api.census.gov/data'

    def __init__(self, url, session=None):
        super(CensusCatalog, self).__init__(session=session)

    @lazy_property
    def datasets(self):
        pass


class CensusDataset(RestApiBase):

    def __init__(self, url, key=None, session=None):
        self.url = url
        self.key = key
        super(CensusDataset, self).__init__(session=session)

    @lazy_property
    def variables(self):
        response = self._get(f'{self.url}/variables.json')
        response.raise_for_status()
        df = pd.DataFrame.from_dict(response.json()["variables"]).T
        df.predicateType = df.predicateType.replace(['string', np.nan], 'str')
        return df

    @lazy_property
    def geographies(self):
        response = self._get(f"{self.url}/geography.json")
        return pd.DataFrame(response.json()["fips"])

    @lazy_property
    def groups(self):
        response = self._get(f"{self.url}/groups.json")
        return pd.DataFrame.from_dict(response.json()["groups"])

    def query(self, get, forString, inString=None, key=None):

        if not isinstance(get, list):
            get = [get]

        result = None

        # census api caps each query to 50 get variables
        for c in chunks(sorted(get), 50):

            params = {
                'get': ','.join(c),
                'for': forString,
            }

            if inString:
                params['in'] = inString

            if key or self.key:
                params['key'] = key if key else self.key

            response = self._get(self.url, params=params)
            response.raise_for_status()
#            print(response.url, response.status_code)

            # convert to DataFrame
            chunk_result = pd.DataFrame.from_records(
                response.json()[1:],
                columns=response.json()[0],
            )

            # replace placeholder values
            chunk_result.replace(
                to_replace=r'\-\d{9}',
                value=np.nan,
                regex=True,
                inplace=True,
            )

            # convert each variable to type provided in /variables.json
            type_dict = {
                k: eval(self.variables.loc[k, 'predicateType'])
                for k in chunk_result.columns
                if k not in list(self.geographies.name)
            }
            chunk_result = chunk_result.astype(type_dict, errors='ignore')

            # pull out geographies in columns - for merge and reorganize
            geographies = [
                i for i in chunk_result.columns
                if i in list(self.geographies.name)
            ]

            # combine results if multiple queries were necessary
            if isinstance(result, pd.DataFrame):

                # merge on geographies
                result = pd.merge(result, chunk_result, on=geographies)

            else:
                result = chunk_result

            # (optional) reorganize columns - move geographies first
            result = result[
                geographies +
                [i for i in result.columns if i not in geographies]
            ]

        return result

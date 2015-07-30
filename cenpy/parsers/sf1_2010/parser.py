import os
import pandas as pd
from requests import get

pj = os.path.join
selfpath = os.path.dirname(os.path.realpath(__file__))


class SF1_2010(object):
    def __init__(self, updir, states=[], **kwargs):
        self._year = 2010
        self._dbpaths = [os.path.join(updir, d) for d in os.listdir(updir) ]
        self._dbpaths = [d for d in self._dbpaths if os.path.isdir(d)]
        sts = [s.split('/')[-1][0:2] for s in self._dbpaths]
        self.states = {s:FileDB(d, parse=False, state=s) for s in sts}
        self._maindir = updir
        self.variables = pd.read_csv(os.path.join(selfpath, 'fields.csv'))
        self.geographies = pd.read_csv(os.path.join(selfpath, 'geographies.csv'))

    def __repr__(self):
        return 'Connection to ' + self._maindir

    def query(get, geo_unit, geo_filter):
        """return information from a census fractured file database"""

    def get_documentation(year=2010, outdir='~'):
        if year == 2010:
            tdoc = get('https://www.census.gov/prod/cen2010/doc/sf1.pdf')
            with open(os.path.expanduser(outdir), 'wb') as docout:
                docout.write(tdoc)
            print('File written to ', os.path.expanduser(outdir))
            return None
    
    def query(get, geolevel, filt):
        filt = [False] * len(self.packlist)
        for col in cols:
            filt = [p or i.startswith(col) for p,i in zip(filt,self.packlist.index)]

        qpack = self.packlist[filt].copy()
        pass

class FileDB(object):
    def __init__(self, sfdir, **kwargs):
        self._datadir = sfdir
        self._files = os.listdir(self._datadir)
        if 'state' in kwargs:
            self.state = kwargs.pop('state').lower()
        self._datafiles = [x for x in self._files if x.endswith('.sf1') and 'geo' not in x]
        self._geoheader = [x for x in self._files if 'geo' in x]
        self._packlist = [x for x in self._files if 'packinglist' in x]

        if len(self._geoheader) > 1:
            raise KeyError('Multiple Geographic Header Files found')
        elif len(self._geoheader) < 1:
            raise KeyError('No Geographic Header File found')
        if len(self._packlist) > 1:
            raise KeyError('Multiple Packing List found')
        elif len(self._geoheader) < 1:
            raise KeyError('No Packing List found')

        self._geoheader = self._geoheader[0]
        self._packlist = self._packlist[0]

        if 'parse' in kwargs:
            parse = kwargs.pop('parse')
        else:
            parse = True
        # IMPLEMENT KWARGS PASSING HERE
        if parse:
           self._parse_heads()
        else:
            self._parsed = False

    ##################
    # HELPER PARSERS #
    ##################

    def _readfile(self, fnum):
        # split each row by spaces to get the table:length pairs
        # check if any of those start with the table we need. If so, we want it
        filt = [any([x.startswith(''.join([str(fnum), ':'])) for x in l.split(' ')]) \
                for l in self.packlist['spec']]
        tablespec = self.packlist[filt]
        
        #then, starting from the top, build the columns for the file
        cols = ['FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'LOGRECNO']
        for tabl, spec in zip(tablespec['table'], tablespec['spec']):
            segcells = spec.split(' ')
            start =1
            for c in segcells:
                t, end = c.split(':')
                if t != str(fnum):
                    start += int(end)
                else:
                    cols.extend([tabl + '_' + str(x).rjust(4, '0') for x in range(start, start + int(end))])
        fpath = self._datadir + '/' + self.state + str(fnum).rjust(5, '0') + '2010.sf1'
        print cols
        data = pd.read_csv(fpath, names=cols, header=False)
        return data

    def _parse_heads(self):
        self.packlist = self._parse_packlist(pj(self._datadir, self._packlist))
        self.geoheader = self._parse_geoheader(pj(self._datadir, self._geoheader))
        self._parsed = True

    def _parse_packlist(self, packlist_path):
        with open(packlist_path) as packfp:
            header = [packfp.readline().strip('\n') for line in range(0, 7)]
            header = [line.strip(' ').split(':') for line in header if '#' not in line]
            header = {field[0]: field[1].lstrip(' ') for field in header}

            packfp.readline()
            bodylist = []
            info = False
            infolist = []
            hashlines = 0

            while hashlines < 2:
                line = packfp.readline().strip('\n')
                if line == '#' * 80:
                    hashlines += 1
                elif line == '':
                    info = not info
                elif info:
                    infolist.append(line)
                elif '|' in line:
                    bodylist.append(line)

            bodylist = [[e for e in l.split('|') if e != ''] for l in bodylist]
            bodylist = pd.DataFrame(bodylist)
            bodylist.columns = ['table', 'spec']
        return bodylist

    def _parse_geoheader(self, geoheader_path, **kwargs):
        colspecs, cols = self._packinfo()
        if 'columns' in kwargs:
            cols = kwargs.pop('cols')
        if 'colspecs' in kwargs:
            colspecs = kwargs.pop('colspecs')
        data = pd.read_fwf(geoheader_path, colspecs=colspecs, header=False, **kwargs)
        data.columns = cols
        return data

    def _packinfo(self):
        """
        Generate the packing tuples for the 2010 short form geoheader
        """
        pl = pd.read_csv(''.join([selfpath, '/packlist.csv']))
        return ([(start, start + skip) for start, skip in zip(pl['start'],
                pl['fieldsize'])], pl['reference'].tolist())

    ##########
    # PUBLIC #
    ##########

    def query(self, get, geo_level, geo_filt, ptupes=None):
        """Query a file DB for a set of columns"""

        # New Strategy: 
        # 1. Figure out which files to grab
        # 2. For each file, _readfile() and drop unwanted
        # 3. join file to key
        # 4. return joined dataset

        if not self._parsed:
            self._parse_heads()
        dat = self.geoheader[self.geoheader['SUMLEV'] == geo_level]['LOGRECNO'].copy()
        dat = pd.DataFrame(dat)
        print dat.head()
        filt = [False] * len(self.packlist)
        for col in get:
            filt = [p or i == col for p, i in zip(filt,self.packlist['column'])]
        print any(filt)
        qpack = self.packlist[filt].copy()
        print qpack
        
        allcoldict = {s:[field for field in self.packlist[self.packlist['segment']==s]
                ['column']] for s in self.packlist['segment']}
        print allcoldict
        pulls = {s:[field for field in qpack[qpack['segment'] == s]['column']] for s in qpack['segment']}
        print pulls
        
        for s,cols in pulls.iteritems():
            fname = self.state + s.rjust(5, '0') + '2010.sf1'
            print fname
            allcols = ['FILEID', 'STUSAB', 'CHARITER', 'CIFSN', 'LOGRECNO']
            allcols.extend(allcoldict[s])
             
            #we want logrecno + every column in that file
            tograb = ['LOGRECNO']
            tograb.extend(cols)
            print tograb
            
            #we don't want everything else
            nograb = [x for x in allcols if x not in tograb]
            
            tdf = pd.read_csv(os.path.join(self._datadir, fname) , names=allcols,header=None)
            tdf.drop(nograb, axis=1, inplace=True)
            print tdf.head()
            dat = dat.merge(tdf, how='left', on='LOGRECNO')
            print dat.head()
        return dat

        ##now, need a way to open just these files in fnames, grab only relevant columns, and return them to the
        ##db-level queryer. remember, this method is of a state filedatabase.
    
    #########
    # MAGIC #
    #########

    def __repr__(self):
        return 'Connection to ' + self._datadir

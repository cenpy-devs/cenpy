# census-pandas
For now, idle exploration around making it easier to use the pandas library to analyze Census data.
 
## Background
A while ago, [Hunter Owens asked](https://twitter.com/hunter_owens/status/565209535552692224) 
if we knew about anyone using the [pandas](http://pandas.pydata.org/) data analysis package
with the Census Reporter API. I whipped up some [example code in a gist](https://gist.github.com/JoeGermuska/1ed425c068d540326854)
and went on with things.

Recently I started fooling around with it a little more and decided to put it on Github in case anyone else was interested. 
For a brief moment I considered trying to port [Ezra Glenn's acs.R package](http://dusp.mit.edu/uis/publication/acsr-r-package-neighborhood-level-data-us-census), 
but I quickly realized that that is an enormous accomplishment and honestly, I don't do enough data analysis on a routine basis to be motivated.

For now, it uses the [Census Reporter API](https://github.com/censusreporter/census-api/blob/master/API.md) for data, but it might make sense to use the [official Census API](http://www.census.gov/data/developers/data-sets/acs-survey-5-year-data.html), since right now CR only has one year worth of data.

## Usage
For now, there's really one method, <code>get_dataframe</code>. Here's how it works:
```
get_dataframe(tables='B01003',geoids='040|01000US',col_names=True,geo_names=True,include_moe=True)
df.head()
```

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right">
      <th></th>
      <th>name</th>
      <th>Total</th>
      <th>B01003001_moe</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>04000US01</th>
      <td>    Alabama</td>
      <td>  4833722</td>
      <td> 0</td>
    </tr>
    <tr>
      <th>04000US02</th>
      <td>     Alaska</td>
      <td>   735132</td>
      <td> 0</td>
    </tr>
    <tr>
      <th>04000US04</th>
      <td>    Arizona</td>
      <td>  6626624</td>
      <td> 0</td>
    </tr>
    <tr>
      <th>04000US05</th>
      <td>   Arkansas</td>
      <td>  2959373</td>
      <td> 0</td>
    </tr>
    <tr>
      <th>04000US06</th>
      <td> California</td>
      <td> 38332521</td>
      <td> 0</td>
    </tr>
  </tbody>
</table>

As the syntax suggests, you can pass multiple tables: you really should use an array in that case, but if you pass a string, it adapts. 

The same goes for geoids: pass a string or an array of strings. As the example demonstrates, you can select a group of related geographies using Census Reporter's syntax of <code>sumlev|container-geoid</code>.


## Contributing
I'm open to input and pull requests. Who knows where this will go.

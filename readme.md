## HCSIS inspection scraper

Python scraper built with Scrapy that scrapes inspection and sanction data from DHS's [HCSIS directory](https://www.hcsis.state.pa.us/hcsis-ssd/ServicesSupportDirectory/Providers/GetProviders?alphabet=A).

The website uses Microsoft's [ASP.net framework](https://metacpan.org/pod/release/ECARROLL/HTML-TreeBuilderX-ASP_NET-0.09/lib/HTML/TreeBuilderX/ASP_NET.pm).

## Install & run

1) Open terminal, cd into this project folder and run:
```
pipenv install
```

2) To scrape inspections: From the project root, run the command below. This will create a SQLite DB (hcsis.db) and a CSV file 

```
cd hcsis && scrapy crawl inspections -o inspections.csv
```

3) To scrape sanctions: From the project root, run the command below. This will create a SQLite DB (hcsis.db) and a CSV 
file 

```
cd hcsis && scrapy crawl sanctions -o sanctions.csv
```
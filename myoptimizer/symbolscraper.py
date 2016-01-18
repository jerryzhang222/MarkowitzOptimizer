from bs4 import BeautifulSoup
from mechanize import Browser
import csv
import numpy as np

def getTwentySymbols(startNum):
    mech = Browser()
    url = "https://finance.yahoo.com/lookup/stocks?bypass=true&s=b&t=S&b=" + str(startNum) + "&m=US"
    page = mech.open(url)
    
    html = page.read()
    soup = soup = BeautifulSoup(html, 'html.parser')
    table = soup.find("table",{"class" : "yui-dt"})
    
    for row in table.findAll("tr")[1:]:
        col = row.findAll("td")
        ticker = col[0].find("a").string
        name = str(col[1]).replace('<td>','').replace('</td>','').replace('"','')
        try:
            category = col[4].find("a").string.replace('"','')
        except AttributeError:
            category = ''
        exchange = str(col[5]).replace('<td>','').replace('</td>','')
        
        resultFile = open("symbolOutput.csv",'a')
        wr = csv.writer(resultFile)
        wr.writerow([ticker, name, category, exchange])
        resultFile.close()
        
def runScraper(endNum):
    for startNum in list(np.arange(2000, endNum, 20)):
        try:
            getTwentySymbols(startNum)
        except:
            pass
        
        
runScraper(4267)
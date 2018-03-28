# This is a template for a Python scraper on morph.io (https://morph.io)
# including some code snippets below that you should find helpful

# import scraperwiki
# import lxml.html
#
# # Read in a page
# html = scraperwiki.scrape("http://foo.com")
#
# # Find something on the page using css selectors
# root = lxml.html.fromstring(html)
# root.cssselect("div[align='left']")
#
# # Write out to the sqlite database using scraperwiki library
# scraperwiki.sqlite.save(unique_keys=['name'], data={"name": "susan", "occupation": "software developer"})
#
# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries.
# You can use whatever libraries you want: https://morph.io/documentation/python
# All that matters is that your final data is written to an SQLite database
# called "data.sqlite" in the current working directory which has at least a table
# called "data" .

from selenium import webdriver
import time
import pandas as pd
import unidecode
import scraperwiki

# PhantomJS support
driver = webdriver.PhantomJS()

driver.get('https://www.glassdoor.com/index.htm')

# window size to make sure javascript parts does not get hidden
driver.set_window_size(1280, 1024)

# To type in job title and location
driver.find_element_by_css_selector('#KeywordSearch').send_keys('Data Scientist')
driver.find_element_by_css_selector('#LocationSearch').clear()
driver.find_element_by_css_selector('#LocationSearch').send_keys('Hong Kong')
driver.find_element_by_css_selector('#HeroSearchButton').click()

# Initializer for the while loop. Will be false once reaches end of page.
end = True

# Initialize columns for data frame before putting together a data frame
# Long term plan is to automate this with Morph.io and pull data using API

cols = ['Title', 'Company', 'Link', 'Rating', 'Job_Description', 'Size', 'Founded', 'Company_Type', 'Industry',
        'Revenue', 'CEO', 'Recommend', 'Approve']

df = pd.DataFrame(columns=cols)

while end:
    links = driver.find_elements_by_css_selector('#MainCol .flexbox .jobLink')

    # j is used to enumerate the links that contains the company names, ratings, and the job links

    for j, link in enumerate(links):
        time.sleep(2)
        link.click()
        # Col 1: Job Title
        job_titles = link.text

        try:
            # to cancel the annoying pop up that tries to prevent scrapers
            driver.find_element_by_class_name('mfp-close').click()
        except:
            pass

        # Col 2: Company Name
        # Decoding some accents
        companies = unidecode.unidecode(link.find_elements_by_xpath('//div[@class="flexbox empLoc"]/div[1]')[j].text.split("–")[0].strip())
        # Below has issue, those ith HOT or NEW won't be read as posted date
        # print('Posted: ',link.find_elements_by_xpath('//span[@class="minor"]')[i].text)

        # Col 3: Link to the job
        job_links = link.find_elements_by_xpath('//div[@class="flexbox"]/div/a')[j].get_attribute('href')
        time.sleep(5)

        # Col 4: Ratings
        try:
            ratings = link.find_element_by_xpath('//span[@class="compactStars margRtSm"]').text
        except:
            ratings = ''
            pass

        # Tab 1: Job description
        # Col 5: Job description
        try:
            descriptions = unidecode.unidecode(link.find_element_by_xpath('//div[@class="jobDescriptionContent desc module pad noMargBot"]').text)
        except:
            time.sleep(20)
            descriptions = unidecode.unidecode(link.find_element_by_xpath('//div[@class="jobDescriptionContent desc module pad noMargBot"]').text)

            pass

        # Tab 2: Company Tab
        # Successfully selected xpath same level based on condition
        # https://stackoverflow.com/questions/26963092/selecting-values-in-xpath-depending-on-values-at-same-level
        try:
            driver.find_element_by_xpath('//li[@data-target = "CompanyContainer"]').click()

            # Col 6: Size
            sizes = link.find_element_by_xpath('//div[@class = "infoEntity"][label[.] = "Size"]/'
                                                     'span[@class = "value"]').text


            # Col 7: Founded
            founded_years = link.find_element_by_xpath('//div[@class = "infoEntity"][label[.] = "Founded"]/'
                                                             'span[@class = "value"]').text


            # Col 8: Type
            types = link.find_element_by_xpath('//div[@class = "infoEntity"][label[.] = "Type"]/'
                                                     'span[@class = "value"]').text.replace("Company - ", "")


            # Col 9: Industry
            industries = link.find_element_by_xpath('//div[@class = "infoEntity"][label[.] = "Industry"]/'
                                                          'span[@class = "value"]').text


            # Col 10: Revenue
            revenues = link.find_element_by_xpath('//div[@class = "infoEntity"][label[.] = "Revenue"]/'
                                                        'span[@class = "value"]').text

        except:
            sizes = ''
            founded_years = ''
            types = ''
            industries = ''
            revenues = ''
            pass

        # Tab 3: Rating Tab (only this tab needs try except)
        try:
            driver.find_element_by_xpath('//li[@data-target = "RatingContainer"]').click()
            # Col 11: CEO
            # Decoding accents in CEO name
            CEOs = unidecode.unidecode(link.find_element_by_xpath('//div[@class = "tbl gfxContainer"]/div[3]/div[@class="tbl"]'
                                                    '/div[2]/div[1]').text)
            # Col 12: Recommend
            recommends = link.find_element_by_xpath('//div[@id = "EmpStats_Recommend"]').get_attribute('data-percentage')

            # Col 13: Approve of CEO
            approves = link.find_element_by_xpath('//div[@id = "EmpStats_Approve"]').get_attribute('data-percentage')
        except:
            CEOs = ''
            recommends = ''
            approves = ''
            pass

        df = df.append({
            'Link': job_links,
            'Title': job_titles,
            'Company': companies,
            'Rating': ratings,
            'Job_Description': descriptions,
            'Size': sizes,
            'Founded': founded_years,
            'Company_Type': types,
            'Industry': industries,
            'Revenue': revenues,
            'CEO': CEOs,
            'Recommend': recommends,
            'Approve': approves

        }, ignore_index=True)

        time.sleep(2)

    # To prevent selenium returning stalemate element
    # https://stackoverflow.com/questions/45002008/selenium-stale-element-reference-element-is-not-attached-to-the-page
    try:
        driver.find_element_by_css_selector('.next a').click()
    except:
        end = False
        break

# If this is our first run, the database won't exist yet.
# So wrap in a try block.

scraperwiki.sql.save(
        unique_keys=['Link'], data=df, table_name="data"
)

time.sleep(5)
driver.close()


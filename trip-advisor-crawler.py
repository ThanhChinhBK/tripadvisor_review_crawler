
import argparse
import os
import re
import codecs

import urllib.request as request
import urllib.error as urlerror
import socket
from contextlib import closing
from time import sleep
from bs4 import BeautifulSoup
import json
all_res = []
def download_page(url, maxretries, timeout, pause):
    tries = 0
    htmlpage = None
    while tries < maxretries and htmlpage is None:
        try:
            with closing(request.urlopen(url, timeout=timeout)) as f:
                htmlpage = f.read()
                sleep(pause)
        except (urlerror.URLError, socket.timeout, socket.error):
            tries += 1
    return htmlpage


def getactivityids(domain, activitytype, locationid, timeout, maxretries, pause):
    baseurl = 'http://www.tripadvisor.' + domain + '/'+activitytype+'s-g'
    oastep = 30
    activityids = set()
    citypage = 0
    activityre = re.compile(r'/'+activitytype+'_Review-g([0-9]+)-d([0-9]+)-Reviews')

    while citypage<3:
        if citypage == 0:
            cityurl = '%s%s' % (baseurl, locationid)
        else:
            cityurl = '%s%s-oa%s' % (baseurl, locationid, citypage * oastep)
        print(cityurl)
        htmlpage = download_page(cityurl, maxretries, timeout, pause)

        if htmlpage is None:
            print('Error downloading the city URL: ' + cityurl)
            break
        else:
            pageids = set(activityre.findall(htmlpage.decode('utf-8')))
            allin = True
            for id_ in pageids:
                if not id_ in activityids:
                    allin = False
                    break
            if allin:
                break
            activityids.update(pageids)
            citypage += 1

    return activityids


def getreviewids(domain, activitytype, cityid, activityid, timeout, maxretries, maxreviews, pause):
    baseurl = 'http://www.tripadvisor.' + domain + '/'+activitytype+'_Review-g'
    orstep = 5
    reviewids = set()
    activitypage = 0
    reviewre = re.compile(r'/ShowUserReviews-g%s-d%s-r([0-9]+)-' % (cityid, activityid))
    retries = 5
    while True:
        if maxreviews > 0 and len(reviewids) >= maxreviews:
            break
        if activitypage == 0:
            activitiyurl = '%s%s-d%s' % (baseurl, cityid, activityid)
        else:
            activitiyurl = '%s%s-d%s-or%s' % (baseurl, cityid, activityid, activitypage * orstep)
        print(activitiyurl)
        htmlpage = download_page(activitiyurl, maxretries, timeout, pause)
        
        if htmlpage is None:
            print('Error downloading the URL: ' + activitiyurl)
            break
        else:
            pageids = set(reviewre.findall(htmlpage.decode('utf-8')))
            allin = True
            print(pageids)
            for id in pageids:
                if not id in reviewids:
                    allin = False
                    break

            if allin:
                if retries:
                    retries -= 1
                else:
                    break
            if maxreviews > 0 and len(reviewids) + len(pageids) > maxreviews:
                n = len(reviewids) + len(pageids) - maxreviews
                pageids = list(pageids)
                del pageids[-n:]
                pageids = set(pageids)

            reviewids.update(pageids)
            activitypage += 1

    return reviewids


def getreview(domain, cityid, activity, reviewid, timeout, maxretries, basepath, force, pause):
    baseurl = 'http://www.tripadvisor.' + domain + '/ShowUserReviews-g'
    reviewurl = '%s%s-d%s-r%s' % (baseurl, cityid, activity, reviewid)

    path = os.sep.join((basepath, domain, str(cityid), str(activity)))
    filename = os.sep.join((path, str(reviewid) + '.json'))
    if force or not os.path.exists(filename):
        htmlpage = download_page(reviewurl, maxretries, timeout, pause)

        if htmlpage is None:
            print('Error downloading the review URL: ' + reviewurl)
        else:
            
            soup = BeautifulSoup(htmlpage, 'html.parser')
            review = soup.find("script", {"type":"application/ld+json"})
            review = json.loads(review.text)
            review["reviewBody"] = codecs.decode(review["reviewBody"],'unicode-escape', errors='strict')
            review["name"] = codecs.decode(review["name"],'unicode-escape')
            if not os.path.exists(path):
                os.makedirs(path)

            with codecs.open(filename, mode='w') as file:
                #file.write(htmlpage.decode('utf-8'))
                json.dump(review, file, indent=2, ensure_ascii=False)
                all_res.append(review)


activities = ['Hotel','Restaurant']

def main():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='''ID format:
    domain:locationcode
    e.g. com:187768 reviews of hotels in Italy from the com domain
    domain:locationcode:citycode
    e.g. jp:187899:187899 city of Pisa from the jp domain
    domain:locationcode:citycode:hotelcode
    e.g. it:187899:187899:662603 all reviews for a specific hotel from the it domain
    domain:locationcode:citycode:hotelcode:reviewcode
    e.g. it:187899:187899:662603:322965103 a specific review''')
    parser.add_argument('-f', '--force', help='Force download even if already successfully downloaded', required=False,
                        action='store_true')
    parser.add_argument('-a', '--activity', help='Type of activity to crawl (default: %s)' % activities[0], choices=activities,
                        default=activities[0])
    parser.add_argument(
            '-r', '--maxretries', help='Max retries to download a file. Default: 3',
            required=False, type=int, default=3)
    parser.add_argument(
            '-t', '--timeout', help='Timeout in seconds for http connections. Default: 360',
            required=False, type=int, default=360)
    parser.add_argument(
            '-p', '--pause', help='Seconds to wait between http requests. Default: 0.5', required=False, default=0.5,
            type=float)
    parser.add_argument(
            '-m', '--maxreviews', help='Maximum number of reviews per item to download. Default:unlimited',
            required=False,
            type=int, default=-1)
    parser.add_argument(
            '-o', '--out', help='Output base path', required=True)
    parser.add_argument('ids', metavar='ID', nargs='+',
                        help='IDs for which to download reviews')
    args = parser.parse_args()

    basepath = args.out
    if not os.path.exists(basepath):
        os.makedirs(basepath)

    with open(os.path.join(args.out, 'ids.txt'), 'w') as file:
        for id in args.ids:
            print('input: ', id)
            fields = id.split(':')
            domain = fields[0]
            locationid = fields[1]
            if len(fields) == 2:
                activityids = getactivityids(domain, args.activity, locationid, args.timeout, args.maxretries, args.pause)
            elif len(fields) >= 4:
                activityids = [(fields[2], fields[3])]
            for activitylocationid, activityid in sorted(activityids):
                print('crawling: ', ':'.join((domain, locationid, activitylocationid, activityid)))
                if len(fields) == 5:
                    reviewids = [fields[4]]
                else:
                    reviewids = getreviewids(domain, args.activity, activitylocationid, activityid, args.timeout, args.maxretries,
                                             args.maxreviews,
                                             args.pause)
                for reviewid in sorted(reviewids):
                    print('downloading: ', ':'.join((domain, locationid, activitylocationid, activityid, reviewid)))
                    file.write(':'.join((domain, locationid, activitylocationid, activityid, reviewid)))
                    file.write('\n')
                    getreview(domain, activitylocationid, activityid, reviewid, args.timeout, args.maxretries, basepath,
                              args.force,
                              args.pause)


if __name__ == '__main__':
    main()
    json.dump(all_res, open("all_res.json", "w"), indent=2, ensure_ascii=False)

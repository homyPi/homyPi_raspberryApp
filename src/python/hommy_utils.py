import urllib2
class Utils:
      test_internet_url = 'http://www.google.com'
      
      @staticmethod
      def has_internet():
          try:
              response=urllib2.urlopen(Utils.test_internet_url, timeout=1)
              return True
          except urllib2.URLError as err:
              print(err)
          return False
          
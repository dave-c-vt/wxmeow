import sys
from .weather_query3 import noaa
from .pickler import save_meow, load_meow


class wxmeow(object):

    def __init__(self, location):
        self.location = location

        try:
            self.meow, self.age = load_meow(self.location)
            if self.age > 10:
                self.reload()
        except:
            self.reload()


        self.meowplace   = ", ".join([self.meow.city, self.meow.state])
        self.meowobs     = self.meow.jconditions['features'][0]['properties']['textDescription']
        self.meowtemp    = str(int(round(self.cel2fahr(self.meow.jconditions['features'][0]['properties']['temperature']))))
        self.meowdp      = str(int(round(self.cel2fahr(self.meow.jconditions['features'][0]['properties']['dewpoint']))))
        self.meowbp      = str(int(self.pa2inches(self.meow.jconditions['features'][0]['properties']['seaLevelPressure'])))
        self.meowbptrend = self.check_pressure_trend(self.meow.jconditions['features'])


        i = 0
        self.meowfc = [] # forecast icon (sunny, cloudy, etc.)
        self.meowtp = [] # forecast high temp
        self.meowlt = [] # forecast low temp
        self.dayname = [] # forecast element label
        self.detail = [] # detailed forecast

        while i < 5:
            self.dayname.append(self.meow.jforecast['properties']['periods'][i]['name'].lower())
            self.meowfc.append(self.meow.jforecast['properties']['periods'][i]['icon'])
            self.meowtp.append(str(self.meow.jforecast['properties']['periods'][i]['temperature']))
            self.meowlt.append(str(self.meow.jforecast['properties']['periods'][i]['temperature']))
            self.detail.append(
                "<h3>{0}</h3>{1}".format(
                    self.meow.jforecast['properties']['periods'][i]['name'].lower(),
                    self.meow.jforecast['properties']['periods'][i]['detailedForecast']
                )
            )
            i = i + 1


        table = "<table>","</table>"
        tr    = "<tr>","</tr>"
        td    = "<td>","</td>"
        tdc   = "<td class='one'>"

        wxmeow   = "<h1>"+self.meowplace+"<br> <small>is</small> "+self.meowobs+" <small>and</small> "\
                    +self.meowtemp+" F </br></br>Dew point <small>is</small> "+str(self.meowdp)+\
                    " F</br>Pressure <small>is</small> "+self.meowbptrend+" <small>at</small> "+self.meowbp+" inches</h1>"
        self.wxmeow   = wxmeow.lower()

        futureth   = tr[0]+\
                           td[0]+self.dayname[0]+td[1]+\
                           td[0]+self.dayname[1]+td[1]+\
                           td[0]+self.dayname[2]+td[1]+\
                           tdc+self.dayname[3]+td[1]+\
                           tdc+self.dayname[4]+td[1]+\
                     tr[1]
        futurepics = tr[0]+\
                           td[0]+"<img src="+self.meowfc[0].split(" ")[0]+" id='0' />"+td[1]+\
                           td[0]+"<img src="+self.meowfc[1].split(" ")[0]+" id='1' />"+td[1]+\
                           td[0]+"<img src="+self.meowfc[2].split(" ")[0]+" id='2' />"+td[1]+\
                           tdc+"<img src="+self.meowfc[3].split(" ")[0]+" id='3' />"+td[1]+\
                           tdc+"<img src="+self.meowfc[4].split(" ")[0]+" id='4' />"+td[1]+\
                     tr[1]
        futuretemp = tr[0]+\
                           td[0]+self.meowtp[0]+" F"+td[1]+\
                           td[0]+self.meowtp[1]+" F"+td[1]+\
                           td[0]+self.meowtp[2]+" F"+td[1]+\
                           tdc+self.meowtp[3]+" F"+td[1]+\
                           tdc+self.meowtp[4]+" F"+td[1]+\
                     tr[1]
        futuretext = "<tr class='tr0'>"+"<td colspan='3'>"+self.detail[0]+td[1]+tr[1]+\
                     "<tr class='tr1'>"+"<td colspan='3'>"+self.detail[1]+td[1]+tr[1]+\
                     "<tr class='tr2'>"+"<td colspan='3'>"+self.detail[2]+td[1]+tr[1]+\
                     "<tr class='tr3'>"+"<td colspan='3'>"+self.detail[3]+td[1]+tr[1]+\
                     "<tr class='tr4'>"+"<td colspan='3'>"+self.detail[4]+td[1]+tr[1]


        self.javascript()


        futuremeow = self.js+table[0]+futureth+futurepics+futuretemp+futuretext+table[1]
        self.futuremeow = futuremeow.lower()

        print(wxmeow)
        print(futuremeow)
        print("<br><br>")

        save_meow(self.meow)

    def reload(self):
        """
        get a fresh read from NOAA
        """
        self.meow = noaa(self.location)


    def cel2fahr(self,val):
        """
        if value is C, convert to F, otherwise return same
        """
        c_desc = ['degc','c','celsius','centegrade','cel','centigrade']
        if val['unitCode'].split(":")[1].lower() in c_desc:
            try:
                temp = val['value'] * 9/5 + 32
                units = "F"
            except:
                temp = 999
        else:
            temp = val['value']
        return temp


    def pa2inches(self,val):
        """
        if value is Pa, convert to In-Hg, otherwise return
        """
        p_desc = ['pa','pascal']
        if val['unitCode'].split(":")[1].lower() in p_desc:
            try:
                pressure = val['value'] * 0.00029530
                units = "Inches of Mercury"
            except:
                pressure = 999
        else:
            pressure = val['value']
        return pressure


    def check_pressure_trend(self,features):
        """
        check pressure readings for up/down/flat trend
        """
        try:
            p1 = features[1]['properties']['seaLevelPressure']['value']
            p2 = features[0]['properties']['seaLevelPressure']['value']
            if p1 > p2:
                trend = "falling"
            elif p1 < p2:
                trend = "rising"
            else:
                trend = "stable"
        except:
            trend = "whatever"

        return trend

    def persist():
        # check if zip code file exists < 30 min old
        ## if it does, use it, return the json contents
        ## else, perform a weather query
        """ Probably makes sense to
                1. Check DB for up to date data (last 30 min?)
                2. If up to date, lock and load for page display
                3. If not,
                    a. do a set of queries to refresh datas
                    b. store them in DB
                    c. go back to step 1

            This means, need to develop
                1. a Db schema for wxmeow
                2. functions to write/read from schema
                3. probably some auto refresh for known locations, to keep the responses faster for all the mega fans of wxmeow


        """

        pass


    def javascript(self):
        """
        text output of javascript functions.
        there must be a better way, but who cares...
        """

        javascript = """
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script>
           $(document).ready(function(){
                $("#0").click(function(){
                    $(".tr0").show("fast");
                    $(".tr1").hide("fast");
                    $(".tr2").hide("fast");
                    $(".tr3").hide("fast");
                    $(".tr4").hide("fast");
                });
                $("#1").click(function(){
                    $(".tr0").hide("fast");
                    $(".tr1").show("fast");
                    $(".tr2").hide("fast");
                    $(".tr3").hide("fast");
                    $(".tr4").hide("fast");
                });
                $("#2").click(function(){
                    $(".tr0").hide("fast");
                    $(".tr1").hide("fast");
                    $(".tr2").show("fast");
                    $(".tr3").hide("fast");
                    $(".tr4").hide("fast");
                });
                $("#3").click(function(){
                    $(".tr0").hide("fast");
                    $(".tr1").hide("fast");
                    $(".tr2").hide("fast");
                    $(".tr3").show("fast");
                    $(".tr4").hide("fast");
                });
                $("#4").click(function(){
                    $(".tr0").hide("fast");
                    $(".tr1").hide("fast");
                    $(".tr2").hide("fast");
                    $(".tr3").hide("fast");
                    $(".tr4").show("fast");
                });
            });
</script>
        """
        self.js = javascript


if __name__ == "__main__":
    wxmeow(sys.argv[1])

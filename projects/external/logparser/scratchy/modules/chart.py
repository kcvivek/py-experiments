
import os, os.path, sys, string, types
from common import *
from shutil import copyfile
from pychartdir import *

HOUR_LABELS = ('12 AM', '01 AM', '02 AM', '03 AM', '04 AM', '05 AM', '06 AM', '07 AM', '08 AM', '09 AM', '10 AM', '11 AM',
               '12 PM', '01 PM', '02 PM', '03 PM', '04 PM', '05 PM', '06 PM', '07 PM', '08 PM', '09 PM', '10 PM', '11 PM')

TRUNCATE_LABEL_LEN = 15

##PIE_COLORS = ("red", "green", "yellow", "blue", "yellow", "red", "green") #, int(0xbbbbbb), int(0xFFCC33))

##PIE_THRESHOLD = 0.05  # don't label slices that are smaller than this (5%)

NODATA_IMG = "nodata.png"

YMAX = 0
YMIN = 999999999

PT_SIZE_LEGEND = 8
PT_SIZE_LABEL = 8
PT_SIZE_TITLE = 10
LAYER_DEPTH = 5 # 3D dimension depth for bar charts
LABEL_ANGLE = 22

class Chart:
    def __init__(self, hit_color, page_color, bandwidth_color, bg_color,
                 alt_bg_color, chart_height, path, verbose):
        self.__hit_color = self.color_to_hex(hit_color)
        self.__page_color = self.color_to_hex(page_color)
        self.__bandwidth_color = self.color_to_hex(bandwidth_color)
        self.__bg_color = self.color_to_hex(bg_color)
        self.__bg_color2 = self.color_to_hex(alt_bg_color)
        self.__chart_height = chart_height
        self.verbose = verbose
        self.path = path
    
    def color_to_hex(self, html_color):
        # return the hex equivalent of the html color
        # that is, #ffffff -> 0xfffff
        # if html_color does not begin w/ # then it is returned
        # as is.
        if html_color and html_color[0] == '#':
            return int(html_color[1:], 16)
        return html_color

    def __get_width(self, xnum):
        return xnum * 27 + 75 # * 50 + 75

    def __get_ydensity(self, ymin, ymax):
        #experimental
        diff = int(ymax) - int(ymin)
        if diff < 1000:
            return 100
        if diff < 10000:
            return 90
        elif diff < 1000000:
            return 75
        elif diff < 100000000:
            return 50
        else:
            return 25
        
    def __get_max_label_len(self, height):
        return height / 20


    # width = 0.75 x fontSize x noOfCharacters
    # width = c.getDrawArea().text3(myLabelText, font, fontSize).getWidth() 
    def __get_plot_height(self, height, labels):
        maxlen = 0
        for label in labels:
            if len(label) > maxlen: maxlen = len(label)


        return height - 70 - (3 * maxlen)
        ## return height - 85 # hourly - 5 chars
        ## return height - 77 # daily - 2 chars
        ## return height - 94 # dow - 9 chars


    def __create_xychart(self, filename, width, height, title, xtitle, ytitle,
                         xlabels, hits, pages, bytes):
        # creates a new XYChart object initialized with a size width x height
        # and titles
        if not xlabels:
            # copy a blank image to loc chart path
            try:
                copyfile(os.path.join("misc", NODATA_IMG),
                     os.path.join(self.path, filename))
            except Exception, e: pass
            return 0


        chart = XYChart(width, height)

        chart.yAxis().setTitle(ytitle)
        #chart.xAxis().setTitle(xtitle)  # ignored since ChartDir ad displaces title
        chart.addTitle2(TopCenter, title, "", PT_SIZE_TITLE)
        legend = chart.addLegend(60, 12, 0, "", PT_SIZE_LEGEND)
        legend.setBackground(Transparent)

        plotHeight = self.__get_plot_height(height, xlabels)
        #print plotHeight

        chart.setPlotArea(50, 48, width-50, plotHeight).setBackground(self.__bg_color,
                                                                      self.__bg_color2)

        chart.xAxis().setLabels(list(xlabels) + [""])
        chart.xAxis().setLabelStyle("", PT_SIZE_LABEL)
        chart.yAxis().setAutoScale()
        chart.xAxis().setLabelStyle().setFontAngle(LABEL_ANGLE)

        #legend.setMargin(10)

##        if pages:
##            numitems = len(pages)
##        elif hits:
##            numitems = len(hits)
##        elif bytes:
##            numitems = len(bytes)

        barwidth = 17

        if pages:
            bar_layer = chart.addBarLayer(pages, self.__page_color, "Pages", LAYER_DEPTH)
            bar_layer.setBarWidth(barwidth)
        if hits:
            bar_layer = chart.addBarLayer(hits, self.__hit_color, "Hits", LAYER_DEPTH)
            bar_layer.setBarWidth(barwidth)
        if bytes:
            bar_layer = chart.addBarLayer(bytes, self.__bandwidth_color, "Bandwidth (kb)", LAYER_DEPTH)
            bar_layer.setBarWidth(barwidth)




        try:
            chart.makeChart(os.path.join(self.path, filename))
            return 1
        except:
            print "Error creating chart: %s" % filename
            return 0



    def create_hourly_chart(self, data):
        if self.verbose: print ">> Creating hourly chart"

        pages = []
        hits = []
        bytes = []
        #ymax = YMAX
        #ymin = YMIN
        for i in range(24):
            row = data.get(i, {'hits': 0, 'pages': 0, 'bytes':0})
            pages.append(row['pages'])
            hits.append(row['hits'])
            bytes.append(get_kb(row['bytes']))

            #ymax = max(ymax, row['hits'], row['pages'], bytes[-1])
            #ymin = min(ymin, row['hits'], row['pages'], bytes[-1])

        x = 700
        y = 350
  
        return self.__create_xychart("hourly.png",
                                     x,
                                     y,
                                     "Hourly Usage",
                                     "Hour of Day",
                                     "Pages, Hits, Bandwidth (kb)",
                                     HOUR_LABELS,
                                     hits,
                                     pages,
                                     bytes)
        


    def create_day_of_week_chart(self, data):
        if self.verbose: print ">> Creating day_of_week chart"
        
        pages = []
        hits = []
        bytes = []
        days = []
        #ymax = YMAX
        #ymin = YMIN
        for i in (6,0,1,2,3,4,5):
            row = data.get(i, {'hits': 0, 'pages': 0, 'bytes':0})
            days.append(DAYS[i])
            pages.append(row['pages'])
            hits.append(row['hits'])
            bytes.append(get_kb(row['bytes']))

            #ymax = max(ymax, row['hits'], row['pages'], bytes[-1])
            #ymin = min(ymin, row['hits'], row['pages'], bytes[-1])

        x = 300
        y = 300

        return self.__create_xychart("day_of_week.png",
                                     x,
                                     y,
                                     "Usage By Day of Week",
                                     "Day of Week",
                                     "Pages, Hits, Bandwidth (kb)",
                                     days,
                                     hits,
                                     pages,
                                     bytes)
   


    def create_summary_chart(self, fname, summary):
        if self.verbose: print ">> Creating summary chart"
        
        pages = []
        hits = []
        bytes = []
        months = []
        count = len(summary)
        #ymax = YMAX
        #ymin = YMIN
        for i in range(count):
            dict = summary[i]
            months.append(MONTHS[dict['month']][:3] + "-" + str(dict['year']))
            pages.append(dict['pages'])
            hits.append(dict['hits'])
            bytes.append(get_kb(dict['bytes']))
            
            #ymax = max(ymax, hits[-1], pages[-1], bytes[-1])
            #ymin = min(ymin, hits[-1], pages[-1], bytes[-1])
            

        x = max(self.__get_width(len(months)), 152)
        y = 300

        return self.__create_xychart(fname,
                                     x,
                                     y,
                                     "Summary",
                                     "Month",
                                     "Pages, Hits, Bandwidth (kb)",
                                     months,
                                     hits,
                                     pages,
                                     bytes)
       

    def create_daily_chart(self, sorted):
        if self.verbose: print ">> Creating daily chart"
        
        pages = []
        hits = []
        bytes = []
        dates = []

        count = len(sorted) 
        #ymax = YMAX
        #ymin = YMIN
        for i in range(count):
            row = sorted[i]
            dates.append(str(row['day_of_month']))
            pages.append(row['pages'])
            hits.append(row['hits'])
            bytes.append(get_kb(row['bytes']))

            #ymax = max(ymax, row['hits'], row['pages'], bytes[-1])
            #ymin = min(ymin, row['hits'], row['pages'], bytes[-1])

        x = self.__get_width(count)
        y = 300


        return self.__create_xychart("daily.png",
                                     x,
                                     y,
                                     "Daily Usage",
                                     "Day",
                                     "Pages, Hits, Bandwidth (kb)",
                                     dates,
                                     hits,
                                     pages,
                                     bytes)
                                     

    def create_sorted_chart(self, filename, title, key, xtitle, ytitle,
                            sorted, cols, otherdict=None):
        # create a 3d bar chart
        #
        # filename: file to write (relative to report_dir)
        # title, xtitle, ytitle: the main title and axis title strings
        # sorted: a sorted list of dictionaries, each w/ a __key__ key
        #         and any number of other keys (i.e. hits, bytes, etc)
        # cols: a string ("hits") or sequence ( ['hits', 'bytes' ] )
        #       of data to include in chart
        # otherdict: data to use for the "Other" data, if applicable
        #            if not None, the otherdict should include key/val
        #            for each name in the COLS string/sequence
        if self.verbose: print ">> Creating %s chart" % title

        if type(cols) == types.StringType:
            cols = [cols]

        auxdata = {}
        for col in cols:
            auxdata[col] = []

        labels = []

        count = len(sorted)
        max_label_len = self.__get_max_label_len(self.__chart_height)
        #ymax = YMAX
        #ymin = YMIN
        for i in range(count):
            row = sorted[i]

            label = row[key]
            if not label: continue
            if len(label) > max_label_len + 3:
                label = label[:max_label_len] + "..."
            labels.append(label)
            for col in cols:
                if col == 'bytes':
                    auxdata[col].append(get_kb(row[col]))
                else:
                    auxdata[col].append(row[col])
                #ymax = max(ymax, auxdata[col][-1])
                #ymin = min(ymin, auxdata[col][-1])


        ccount = count
        if otherdict:
            ccount += 1
            labels.append("Other")
            for col in cols:
                if col == 'bytes':
                    auxdata[col].append(get_kb(otherdict[col]))
                else:
                    auxdata[col].append(otherdict[col])


        x = self.__get_width(count)
        y = self.__chart_height

        return self.__create_xychart(filename,
                                     x,
                                     y,
                                     title,
                                     xtitle,
                                     "Pages, Hits, Bandwidth (kb)",
                                     labels,
                                     auxdata.get('hits'),
                                     auxdata.get('pages'),
                                     auxdata.get('bytes'))
    
                                     

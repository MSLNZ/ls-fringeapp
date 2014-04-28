"""
EFH 15/12/2009
App to process whole files of images

"""
from poly_lasso import PolyLasso
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.pyplot import figure, show
from matplotlib.widgets import Button
from PIL import Image
import numpy
import EasyDialogs
import os.path
import datetime
import shelve
import fringeprocess
import gauge_length

"""
event based
open excel file event calls  N key load_gauge_data
next and previous image events PAGEUP and PAGEDOWN keys next_image, prev_image
redo image event DELETE key
lasso current image activated by left clicking on image, right click calls process_image

calculate gauge lengths following a finish event END key calculate

self.ffrac needs to be a list or dictionary -done
make sure all data is 1st refered to  in __init__ -done

add a text display to show a list of gauges in current file and whether ff have been done
add buttons for basic functions - done

"""



class FringeManager:
    """simple gauge block picking interface and ff calculator"""
    def __init__(self, ax, menu):
        self.axes = ax
        self.figure = ax.figure
        self.canvas = ax.figure.canvas
        self.filetext = self.figure.text(0.5, 0.05, ' ',
               horizontalalignment='center')
        self.fftext = self.figure.text(0.5, 0.02, ' ',
               horizontalalignment='center')
        self.canvas.mpl_connect('button_press_event', self.onpress)
        self.canvas.mpl_connect('key_press_event', self.keypress)

        self.ffrac = {}
        self.gauge_data = []
        self.gauge_data_filename = ''
        self.img_array = []
        self.img_filename = ''
        self.img_index = 0
        self.img_list = []
        self.lasso = None
        self.lasso_active = True
        self.ff_text_dict = {}
        self.gn_text_dict= {}
        self.shelf_filename = ''

        self.fig_menu = menu




    def process_image(self, ax, lasso_line, verts):
        """ called after polylasso finished, processes image and prints ff"""
        #print verts
        print ('process image')
        self.lasso_active = False
        xygb = numpy.fliplr(numpy.asarray(verts)[:3, :])
        self.canvas.draw_idle()
        self.canvas.widgetlock.release(self.lasso)
        del self.lasso
        ffrac,drawdata = fringeprocess.array2frac(self.img_array, xygb, drawinfo=True)
        img_basename = os.path.basename(self.img_filename)
        self.ffrac[img_basename] = ffrac
        self .annotate_fig(drawdata)
        self.ff_text_dict[img_basename].set_text('%6.3f' %(ffrac))
        self.fig_menu.canvas.draw()
        self.canvas.draw()
        text = ('%.6g\t'% ffrac +
                img_basename +
                '\t'+ ('%.5g\t'*(xygb.ravel().size) ) % tuple(xygb.ravel()))
        print (text)
        notes = EasyDialogs.AskString('Notes on fitting')
        if notes == None:
            notes =' '
        timestr = datetime.datetime.now().isoformat(' ')

        text = text + '\t' + timestr + '\t' + notes
        logfile = open(os.path.join(os.path.dirname(self.img_filename),
                                    'fflog.txt'),'a')
        logfile.write(text +'\n')
        logfile.close()
        #also shelve ffrac, drawdata, timestr, notes with img_filename as key

        db = shelve.open(self.shelf_filename)
        db[img_basename] = [ffrac, drawdata, timestr, notes]
        db.close()




    def onpress(self, event):
        """set up polylasso when mouse is clicked"""
        if self.canvas.widgetlock.locked():
            return
        if event.inaxes is None:
            return
        if self.lasso_active:
            self.lasso = PolyLasso(event.inaxes, self.process_image)
            # acquire a lock on the widget drawing
            self.canvas.widgetlock(self.lasso)
            print ('in lasso')

    def keypress(self, event):
        """maps a key to opening new file
           careful in choice of keys as event is also passed to toolbar
           will replace this with/ add interface buttons
        """
        print (event.key)

        if event.inaxes is None:
            return
        if event.key in ['N', 'n']:
           self.load_gauge_data()
        if event.key == 'pagedown':
            self.next_image()
        if event.key == 'pageup':
            self.prev_image()
        if event.key == 'end':
            self.calculate_output()
        if event.key == 'delete':
            self.redo_image()

    def next_image(self):
        self.img_index = self.img_index + 1
        if self.img_index >= len(self.img_list):
            self.img_index = 0
        self.open_image()

    def prev_image(self):
        self.img_index = self.img_index - 1
        if self.img_index < 0:
            self.img_index = len(self.img_list)-1
        self.open_image()

    def next(self,event):
        self.next_image()

    def prev(self,event):
        self.prev_image()

    def load(self,event):
        self.load_gauge_data()

    def redo(self,event):
        self.redo_image()

    def calc0(self, event):
        self.calculate_output(False)

    def calcAll(self, event):
        self.calculate_output(True)

    def redo_image(self):
        """
        reload image without annotation
        delete from shelf file and reload
        """
        shelfnm = os.path.join(os.path.dirname(self.img_filename), 'info.shf')
        db = shelve.open(shelfnm)
        img_basename = os.path.basename(self.img_filename)

        if db.has_key(img_basename):
            del db[img_basename]
        db.close()
        self.open_image()
        self.lasso_active = True


    def open_image(self):
        """opens image in imagelist at position image_index"""
        img_filename = self.img_list[self.img_index]
        print (img_filename)
        parts = os.path.split(img_filename)
        self.img_filename = os.path.join(parts[0],'cropped',parts[1])
        img = Image.open(self.img_filename)
        img.convert('L')
        self.img_array = numpy.asarray(img)
        if self.img_array.ndim > 2:
            self.img_array = self.img_array.mean(axis=2)
        self.axes.clear()
        self.axes.imshow(self.img_array, cmap = matplotlib.cm.gray)
        self.axes.axis('image')
        self.axes.axis('off')
        img_basename = os.path.basename(self.img_filename)
        self.filetext.set_text(img_basename)
        self.fftext.set_text(' ')
        self.lasso_active = True
        #check if image has an entry in directory's shelf file
        #if so use it to annotate image

        if os.path.exists(self.shelf_filename):
            db = shelve.open(self.shelf_filename)
            if db.has_key(img_basename):
                print ('found ',img_basename, ' on shelf')
                [ffrac, drawdata, timestr, notes] = db[img_basename]
                self.ffrac[img_basename] = ffrac
                self .annotate_fig(drawdata)
                self.lasso_active = False
            db.close()
        self.canvas.draw()

    def load_gauge_data(self):
        """
        prompts user to open file written by excel program, reads it and creates
        a list of images to process
        """
        txt_name = EasyDialogs.AskFileForOpen(message='Select text file written by excel')
        if txt_name:
            self.gauge_data_filename = txt_name

            dt = numpy.dtype([('NominalSize', float),('SerialNo', (str,16)),
                  ('RedDateTime',float),('GreenDateTime',float),('SetId',(str,16)),
                  ('PlatenId', int),('Observer', (str,16)),('Side', int),('ExpCoeff',float),
                  ('Units',(str,16)),('TR',float),('TG',float),('PR', float),('PG', float),
                  ('HR', float),('HG', float),('PlatenPos',int),('RedFileName',(str,256)),
                  ('GreenFileName',(str,256))])

            self.gauge_data = numpy.loadtxt(txt_name, delimiter=',', dtype =dt)
            img_list = list(self.gauge_data[:]['RedFileName'])
            img_list.extend(list(self.gauge_data[:]['GreenFileName']))
            img_list = [name.strip('"') for name in img_list]
            img_list.sort()
            self.img_list = img_list
            self.img_index = 0

            parts = os.path.split(txt_name)
            self.shelf_filename = os.path.join(parts[0],'info.shf')
            print (self.shelf_filename)
            if os.path.exists(self.shelf_filename):
                db = shelve.open(self.shelf_filename)
                for key in db.keys():
                    [ffrac, drawdata, timestr, notes] = db[key]
                    self.ffrac[key] = ffrac
                db.close()
                print (self.ffrac)
            #make list of images on left of figure
            #remove any previous text
            for text in self.gn_text_dict.itervalues():
                text.text = ''
            for text in self.ff_text_dict.itervalues():
                text.text = ''

            ypos = 0.9
            for gauge in self.gauge_data:
                img_basename = os.path.basename(gauge['RedFileName']).strip('"')
                redtext = img_basename[:-17]
                text = self.fig_menu.text(0.65, ypos, redtext,
                            horizontalalignment='left', fontsize=12)
                self.gn_text_dict[img_basename] = text
                try:
                    fftext =  '%6.3f' %(self.ffrac[img_basename])
                except:
                    fftext = 'NA'

                text = self.fig_menu.text(0.85, ypos, fftext,
                            horizontalalignment='left', fontsize=12, color='red')
                self.ff_text_dict[img_basename] = text

                img_basename = os.path.basename(gauge['GreenFileName']).strip('"')
                greentext = img_basename[:-17]
                text = self.fig_menu.text(0.35, ypos, greentext,
                            horizontalalignment='left', fontsize=12)
                self.gn_text_dict[img_basename] = text
                try:
                    fftext =  '%6.3f' %(self.ffrac[img_basename])
                except:
                    fftext = 'NA'

                text = self.fig_menu.text(0.55, ypos, fftext,
                            horizontalalignment='left', fontsize=12, color='green')
                self.ff_text_dict[img_basename] = text

                ypos = ypos-0.03

            self.open_image()

    def annotate_fig(self, drawdata):
        [xy,co,ro,ci,ri,ccen,rcen,pklist,slopep,interceptsp,slopeg,interceptsg] = drawdata

        #imgplot = ax.imshow(SF2,aspect='equal')
        #imgplot.set_cmap('gray')
        self.axes.plot(xy[:,1],xy[:,0],'or')
        self.axes.plot(ccen,rcen,'+c',ms=20)
        self.axes.plot(co,ro,'w-')
        self.axes.plot(ci,ri,'c-')
        for col,peaks in enumerate(pklist):
                x = col*numpy.ones_like(peaks)
                self.axes.plot(x,peaks,'+y')
        maxx = self.img_array.shape[1]
        for cepts in interceptsp:
            self.axes.plot([0,maxx],[cepts,slopep*maxx+cepts],'-m')
        for cepts in interceptsg:
            self.axes.plot([0,maxx],[cepts,slopeg*maxx+cepts],'g-')
        key = os.path.basename(self.img_filename)
        print (key, type(key))
        fftitle =  '%6.3f' %(self.ffrac[key])
        self.fftext.set_text(fftitle)

    def calculate_output(self, output_all_orders):

        out_filename = os.path.join(os.path.splitext(self.gauge_data_filename)[0]+ '-calcs-py.txt')
        out_filename = EasyDialogs.AskFileForSave(message='Select text file to save calculated resuts to',
                                                  savedFileName=out_filename)

        if out_filename:
            fid = open(out_filename,'w')
            for gauge in self.gauge_data:
                redkey = os.path.basename(gauge['RedFileName']).strip('"')
                ffred = self.ffrac[redkey]
                greenkey = os.path.basename(gauge['GreenFileName']).strip('"')
                ffgreen = self.ffrac[greenkey]
                #calculation is always done in metric
                if gauge['Units'].strip('"') != 'Metric':
                    nomsize = gauge['NominalSize'] * 25.4
                    print ("Calculating in Inch system")
                else:
                    nomsize = gauge['NominalSize']
                    #print "Calculating in Metric System"
                print (nomsize)
                RD, GD, bestindex = gauge_length.CalcGaugeLength( nomsize,
                                              gauge['TR'],
                                              gauge['TG'],
                                              gauge['PR'],
                                              gauge['HR'],
                                              ffred*100,
                                              ffgreen*100,
                                              gauge['ExpCoeff'])

                #translate metric values for deviations (nanometres) to imperial values (microinches)
                if gauge['Units'].strip('"') != 'Metric':
                    RD = RD/25.4
                    GD = GD/25.4
                    #print "changing dev to microinch!"

                Observer = 'MTL'

                if output_all_orders:
                    orders = range(0,10)
                else:
                    orders = [5]

                for idev in orders:

                    DiffDev =  RD[idev]- GD[idev]
                    MeanDev = (RD[idev]+ GD[idev])/2.0
                    outtext = '%f,"%s",%.1f,%.1f,%.1f,%.1f,%d,%f,%f,"%s",%u,"%s",%u,%e,"%s",%f,%f,%f,%f,%f,%f,%.2f,%.2f,%d,%d,"%s","%s"\n' \
                           %(gauge['NominalSize'],
                             gauge['SerialNo'],
                             MeanDev,
                             DiffDev,
                             RD[idev],
                             GD[idev],
                             bestindex,
                             gauge['RedDateTime'],
                             gauge['GreenDateTime'],
                             gauge['SetId'],
                             gauge['PlatenId'],
                             'PY',
                             gauge['Side'],
                             gauge['ExpCoeff'],
                             gauge['Units'],
                             gauge['TR'],
                             gauge['TG'],
                             gauge['PR'],
                             gauge['PG'],
                             gauge['HR'],
                             gauge['HG'],
                             ffred*100.0,
                             ffgreen*100.0,
                             0,
                             gauge['PlatenPos'],
                             gauge['RedFileName'],
                             gauge['GreenFileName'])
                    fid.write(outtext)
            fid.close()


if __name__ == '__main__':

    fig = figure(figsize=(8, 6), dpi=80)
    axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])
    fig_menu = figure(figsize=(8,6), dpi=80)

    lman = FringeManager(axes,fig_menu)

    axload = fig_menu.add_axes([0.1, 0.825, 0.3, 0.075])
    axprev = fig_menu.add_axes([0.1, 0.725, 0.3, 0.075])
    axnext = fig_menu.add_axes([0.1, 0.625, 0.3, 0.075])
    axredo = fig_menu.add_axes([0.1, 0.525, 0.3, 0.075])
    axcalc0 = fig_menu.add_axes([0.1, 0.425, 0.3, 0.075])
    axcalcAll = fig_menu.add_axes([0.1, 0.325, 0.3, 0.075])

    bload = Button(axload, 'Load')
    bload.on_clicked(lman.load)

    bnext = Button(axnext, 'Next')
    bnext.on_clicked(lman.next)

    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(lman.prev)

    bredo = Button(axredo, 'Redo')
    bredo.on_clicked(lman.redo)

    bcalc0 = Button(axcalc0, 'Calculate Zero Order')
    bcalc0.on_clicked(lman.calc0)

    bcalcAll = Button(axcalcAll, 'Calculate All Orders')
    bcalcAll.on_clicked(lman.calcAll)


    lman.load_gauge_data()


    show()

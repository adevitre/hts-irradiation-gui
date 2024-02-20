import numpy as np

def renameFiles(directory):
    for f in [f for f in os.listdir(directory) if 'anneal270-12h' in f]:
        pieces = f.split('_')
        newfname = pieces[0]
        for piece in pieces[1:-1]:
            newfname += '_'+piece
        newfname += '_anneal270k-12h.txt'
        
        #print(directory+f, directory+newfname)
        os.rename(directory+f, directory+newfname)

def binAverage(xbins, xdata, ydata):
    yavgs, ystds, yfiltered, xfiltered = [], [], np.array([]), np.array([])
    for (minb, maxb) in zip(xbins[:-1], xbins[1:]):
        cut = (minb < xdata) & (xdata < maxb)
        yavg, ystd = np.nanmean(ydata[cut]), np.nanstd(ydata[cut])
        yavgs.append(yavg)
        ystds.append(ystd)
        stdfilter = (yavg-ystd <= ydata[cut])&(ydata[cut] <= yavg+ystd)
        yfiltered = np.append(yfiltered, ydata[cut][stdfilter])
        xfiltered = np.append(xfiltered, xdata[cut][stdfilter])
    return xbins[:-1]+(xbins[1]-xbins[0])/2., np.array(yavgs), np.array(ystds), xfiltered, yfiltered

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

def timestamp_to_seconds(timestamp):
    hh, mm, ss = timestamp[11:].split('-')
    return float(hh)*3600+float(mm)*60+float(ss)/1e6

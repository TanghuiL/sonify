import pprint
import pdb  # @UnusedImport
from datamapper import TimeSeries, DataObject, DataObjectCollection, DataMapper, DataParser
from renderers.datarenderer import DataRenderer
from renderers.csound01_simple import CsoundSinesSimpleRenderer, CsoundBowedSimpleRenderer,\
    CsoundRenderer
from renderers.midirenderers import MidiRenderer01
import buoyparsers
from datetime import datetime

pp = pprint.PrettyPrinter().pprint

from nose.tools import assert_raises  # @UnresolvedImport (Eclipse)
from math import sin

try:
    from matplotlib import pyplot
except Exception, e:
    print 'pyplot not imported; beware of errors.'
    
def test_datamapper_1():
    # create a TimeSeries
    ts1 = TimeSeries(['datapoint'], sample_rate=60)

    # create a DO and put the TS in it
    do1 = DataObject()
    do1['somedata'] =ts1
    assert do1.keys() == ['somedata']

    # create a DOC and put the DO in it
    doc = DataObjectCollection()
    doc.add(do1)

    # dig down through the levels and get the datapoint we originally inserted
    timeseries = doc.pop()['somedata']
    datapoint = timeseries[0]
    assert(datapoint == 'datapoint')

def test_do_imposes_sample_rate():
   # create a TimeSeries
   ts1 = TimeSeries(['datapoint'])

   # create a DO and put the TS in it
   do1 = DataObject(sample_rate=60)
   do1['somed'] = ts1

   # test the sample_rate of the TimeSeries (which it should derive from the DO)
   assert(do1['somed'].sample_rate == 60)

def test_doc_imposes_sample_rate():
    # create a DO
    do1 = DataObject()

    # create a DOC and put the DO in it
    doc = DataObjectCollection(sample_rate=60)
    doc.add(do1)

    retrieved_do = doc.pop()
    assert(retrieved_do.sample_rate == 60)

def test_ts_range():
    ts = TimeSeries([2,3,1,5,4], ts_range=(0,5))
    assert(ts.ts_range == (0,5))

    ts = TimeSeries([2,3,1,5,4])
    assert(ts.ts_range == (1,5))

def test_DOC_rejects_bad_starter_coll():
    assert_raises(TypeError, DataObjectCollection,1) # 1 is totally not a collection

# Maybe no longer relevant after current refactoring (4/30/13)
# def test_mapping_validation():
#     dicts = [{'sourcekey':'blah'}]
#     assert_raises(AssertionError, Mapping, dicts) # must have targetkey as well
#     dicts = [{'sourcekey':'blah', 'targetkey':1}]
#     assert_raises(AssertionError, Mapping, dicts) # key must refer to string
    
def test_remap_time_index():
    ''' given a starting sample rate of 1.0/60 and a desired sample rate of 1.0/5,
    produce a set of (non-integer) indices to pull from to create our representation.
    '''
    dm = DataMapper(None,ToyDataRenderer()) # Just testing static methods
    remap = dm.remap_time_index
    out_sr = 1/5.0
    in_sr = 1/20.0
    converted = [remap(i,out_sr,in_sr) for i in range(10)]
    assert(converted==[0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25])

def test_remap_range():
    dm = DataMapper(None, ToyDataRenderer())
    inlist = TimeSeries([0, .5, 1])
    original_range = (0,1)
    desired_range = (0,10)
    outlist = dm.remap_range(inlist, original_range, desired_range)
    assert outlist == TimeSeries([0.0, 5.0, 10.0]), 'outlist is '+str(outlist)+': '+str(type(outlist))

    inlist = TimeSeries([1.0, 1.5, 2])
    original_range = (1,2)
    desired_range = (100,110)
    outlist = dm.remap_range(inlist, original_range, desired_range)
    assert outlist == TimeSeries([100.0, 105.0, 110.0]), 'outlist is '+str(outlist)

class ToyDataParser(DataParser):
    def parse(self, listofdicts):
        doc = DataObjectCollection()
        for curdict in listofdicts:
            do = DataObject()
            for key, val in curdict.items():
                do[key] = val
            doc.add(do)
        return doc

class ToyDataRenderer(DataRenderer):
    @property
    def sample_rate(self):
        return self._sample_rate
    @sample_rate.setter
    def sample_rate(self,rate):
        self._sample_rate = rate

    def expose_parameters(self):
        return None
    
    def render(self, doc):
        return "rendered"


class SineDictParser(DataParser):
    ''' Expects a single dict from numbers 0..n to sine timeseries(-1..1) '''
    def parse(self, sines):
        doc = DataObjectCollection()
        do = DataObject()
        for key, sine in sines.items():
           ts = TimeSeries(sine)
           ts.sample_rate = 1
#            ts.ts_range = (-1,1)
           do[key] = ts
        doc.add(do)
        return doc

class MultiSineDictParser(DataParser):
    ''' Expects a list of dicts from numbers 0..n to sine timeseries(-1..1) '''
    def parse(self, sineslist):
        doc = DataObjectCollection()
        for sines in sineslist:
            do = DataObject()
            for key, sine in sines.items():
               ts = TimeSeries(sine)
               ts.sample_rate = 1
               do[key] = ts
            doc.add(do)
        return doc

class SineDictRenderer(DataRenderer):
    ''' Responsible for rendering the doc from SineDictParser '''
    
    def __init__(self):
        # TODO maybe make an intermediate VisualDataRenderer that does this import, so
        # inheritance chain is DataRenderer -> VisualDataRenderer -> SineDictRenderer
        super( SineDictRenderer, self ).__init__()

    @property
    def sample_rate(self):
        return self._sample_rate
    
    @sample_rate.setter
    def sample_rate(self,rate):
        self._sample_rate = rate

    def render(self, doc, showplot=False):
        pyplot.clf()
        while len(doc):
            do = doc.pop()
            for key, ts in do.items():
                x = range(len(ts))
#                 print 'adding plot for', key
                plot = pyplot.plot(x,ts.data, label=key, linewidth=3.0)  # @UndefinedVariable
        if showplot: 
            pyplot.legend()
            pyplot.show()  # @UndefinedVariable
        return plot

    def expose_parameters(self):
        return None
    
def generate_sines(num, length, factor=None):
    ''' Returns a dict from key to list of values (which can become a TimeSeries) '''
    out = {}
    for i in range(num):
        out[i] = []
        if factor:
            factor = ((factor+1)*3 + i)
        else:
            factor = (i+1)*3
        for j in range(length):
            out[i].append(sin((j+factor)/10.3))
    return out


def test_end_to_end_sines():
    parser = SineDictParser()
    sines = generate_sines(3, 4)
    doc = parser.parse(sines)
    renderer = SineDictRenderer()
    plot = renderer.render(doc, showplot=False)
    assert('matplotlib.lines.Line2D' in str(plot))

def test_csound_with_mapping():
    parser = SineDictParser()
    sines = generate_sines(3, 40)
    doc = parser.parse(sines)
    doc.sample_rate = 5
    renderer = CsoundSinesSimpleRenderer()
    mapper = DataMapper(doc, renderer)
    sine_to_csound_map = {0: '0', 1: '1', 2: '2'} # Degenerate case for testing
    transformed_doc = mapper.get_transformed_doc(sine_to_csound_map)
    renderer.render(transformed_doc, filename='/tmp/t.csd', play=False)
    #TODO assert

def test_combine_range():
    ''' Make some sines, modify them to have different ranges, and combine the ranges. '''
    parser = MultiSineDictParser()
    sinelist = []
    for i in range(3):
        sines = generate_sines(3, 3)
        sinelist.append(sines)
    doc = parser.parse(sinelist)
    modified_dos = []
    for i in range(3):
        modified_do = doc.pop()
        modified_do[0] = TimeSeries([(i+1) * v for v in modified_do[0]])
        modified_dos.append(modified_do)
    adjusted_doc = DataObjectCollection(modified_dos)
    old_ranges = [do[0].ts_range for do in adjusted_doc]
    assert old_ranges[0] == (0.5743228620846001, 0.9331896468307443), old_ranges[0]
    assert len(set(old_ranges)) == 3 # All different
    adjusted_doc.combine_range(0)
    new_ranges = [do[0].ts_range for do in adjusted_doc]
    assert new_ranges[0] == (0.2871614310423001, 1.3997844702461166)
    assert len(set(new_ranges)) == 1 # All identical

# Skip this test since the interactivity is a pain during testing
# def test_csound_with_interactive_mapping():
#     parser = SineDictParser()
#     sines = generate_sines(3, 8)
#     doc = parser.parse(sines)
#     pp(doc)
#     doc.sample_rate = 5
#     renderer = CsoundSinesSimpleRenderer()
#     mapper = DataMapper(doc, renderer)
#     interactive_map = mapper.interactive_map(doc, renderer)
#     transformed_doc = mapper.get_transformed_doc(interactive_map)
#     pp(transformed_doc)
#     renderer.render(transformed_doc, filename='/tmp/t.csd', play=False)

def test_csound_with_bowed_string():
    parser = MultiSineDictParser()
    
    # Generate some raw data
    sinelist = []
    for i in range(3):
        sines = generate_sines(3, 128, factor=i)
        sinelist.append(sines)
        
    doc = parser.parse(sinelist)
    doc.sample_rate = 5
    renderer = CsoundBowedSimpleRenderer()
    mapper = DataMapper(doc, renderer)
    sine_to_csound_map = {0: 'amplitude', 1: 'pressure', 2: 'bow_position'}
    transformed_doc = mapper.get_transformed_doc(sine_to_csound_map)
    #pp(transformed_doc)
    renderer.render(transformed_doc, filename='/tmp/t.csd', play=False)
    #TODO assert?

def test_csound_from_orchestra_file():
    parser = MultiSineDictParser()
     
    # Generate some raw data
    sinelist = []
    for i in range(3):
        sines = generate_sines(3, 128, factor=i)
        sinelist.append(sines)
         
    doc = parser.parse(sinelist)
    doc.sample_rate = 5

    orchestra_file = '/Users/egg/Documents/Programming/sonify-env/sonify/csound_files/bowed_string.orc'
    renderer = CsoundRenderer(orchestra_file)
    mapper = DataMapper(doc, renderer)
    sine_to_csound_map = {0: 'amplitude', 1: 'pressure', 2: 'bow_position'}
    transformed_doc = mapper.get_transformed_doc(sine_to_csound_map)
    #pp(transformed_doc)
    renderer.render(transformed_doc, filename='/tmp/t.csd', play=False)
    #TODO assert?

def test_midi_renderer_01():
    print 'testing midi renderer'
    parser = MultiSineDictParser()

    # Generate some raw data
    sinelist = []
    for i in range(3):
        sines = generate_sines(3, 120, factor=i)
        sinelist.append(sines)

    doc = parser.parse(sinelist)
    doc.sample_rate = 5

    renderer = MidiRenderer01()
    mapper = DataMapper(doc, renderer)
    sine_to_midi_map = {0: 74, 1: 75, 2: 76} # sine to cc#
    transformed_doc = mapper.get_transformed_doc(sine_to_midi_map)
    renderer.render(transformed_doc, output_file='/tmp/t.mid')
    #TODO assert?
    
def test_buoy_parser_01():
    #TODO buoyparser takes a long time because it's a huge file. Replace with a smaller sample file.
    parser = buoyparsers.GlobalDrifterParser()
    start = datetime(2000,01,01)
    end = datetime(2001,01,01)
    doc = parser.parse('/Users/egg/Temp/oceancurrents/globaldrifter/buoydata_5001_sep12.dat',
                       start=start, end=end)
#     doc = parser.parse('/Users/egg/Temp/oceancurrents/globaldrifter/buoydata_5001_sep12.dat')
    renderer = SineDictRenderer()
    # No mapping because SineDictRenderer doesn't need one.
    plot = renderer.render(doc, showplot=False)
    assert('matplotlib.lines.Line2D' in str(plot))

def test_buoy_parser_02():
    parser = buoyparsers.GlobalDrifterParser()
    start = datetime(2000,01,01)
    end = datetime(2001,01,01)
    doc = parser.parse('/Users/egg/Temp/oceancurrents/globaldrifter/buoydata_5001_sep12.dat',
                       start=start, end=end)
    doc.combine_range('TEMP')
    orchestra_file = '/Users/egg/Documents/Programming/sonify-env/sonify/csound_files/bowed_string.orc'
    renderer = CsoundRenderer(orchestra_file)
    mapper = DataMapper(doc, renderer)
    sine_to_csound_map = {'LAT': 'amplitude', 'LON': 'pressure', 'TEMP': 'bow_position'}
    transformed_doc = mapper.get_transformed_doc(sine_to_csound_map)
#     import code; code.interact(local=locals())
    renderer.render(transformed_doc, filename='/tmp/t.csd', play=False)
    #TODO assert
